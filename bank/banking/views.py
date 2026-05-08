from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.contrib.auth.forms import UserCreationForm

from .models import Account, Transaction, Client
from .forms import AccountForm, TransactionForm, ClientForm, TransferForm


@login_required
def dashboard(request):
    if request.user.is_superuser:
        accounts = Account.objects.all()
    else:
        client = get_object_or_404(Client, user=request.user)
        accounts = Account.objects.filter(client=client)

    search_query = request.GET.get('q', '').strip()
    balance_filter = request.GET.get('balance', '')

    if search_query:
        accounts = accounts.filter(
            Q(account_number__icontains=search_query)
            | Q(client__user__username__icontains=search_query)
            | Q(client__phone__icontains=search_query)
        )

    if balance_filter == 'positive':
        accounts = accounts.filter(balance__gte=0)
    elif balance_filter == 'negative':
        accounts = accounts.filter(balance__lt=0)

    total_accounts = accounts.count()
    total_balance = accounts.aggregate(Sum('balance'))['balance__sum'] or 0
    total_clients = Client.objects.count() if request.user.is_superuser else 1
    total_transactions = Transaction.objects.filter(account__in=accounts).count()
    recent_transactions = Transaction.objects.filter(account__in=accounts).select_related(
        'account'
    ).order_by('-date')[:5]

    return render(request, 'banking/dashboard.html', {
        'accounts': accounts,
        'total_accounts': total_accounts,
        'total_balance': total_balance,
        'total_clients': total_clients,
        'total_transactions': total_transactions,
        'recent_transactions': recent_transactions,
        'search_query': search_query,
        'balance_filter': balance_filter,
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    clients = Client.objects.select_related('user').annotate(account_count=Count('accounts'))
    accounts = Account.objects.select_related('client', 'client__user').all()
    transactions = Transaction.objects.select_related(
        'account',
        'account__client',
        'account__client__user'
    ).order_by('-date')

    total_balance = accounts.aggregate(Sum('balance'))['balance__sum'] or 0
    credit_total = transactions.filter(transaction_type='CREDIT').aggregate(
        Sum('amount')
    )['amount__sum'] or 0
    debit_total = transactions.filter(transaction_type='DEBIT').aggregate(
        Sum('amount')
    )['amount__sum'] or 0
    positive_accounts = accounts.filter(balance__gte=0).count()
    negative_accounts = accounts.filter(balance__lt=0).count()

    return render(request, 'banking/admin_dashboard.html', {
        'total_clients': clients.count(),
        'total_accounts': accounts.count(),
        'total_transactions': transactions.count(),
        'total_balance': total_balance,
        'credit_total': credit_total,
        'debit_total': debit_total,
        'positive_accounts': positive_accounts,
        'negative_accounts': negative_accounts,
        'recent_clients': clients.order_by('-id')[:5],
        'recent_transactions': transactions[:6],
        'largest_accounts': accounts.order_by('-balance')[:5],
    })


@login_required
def transfer_money(request):
    if request.user.is_superuser:
        from_account_queryset = Account.objects.select_related('client', 'client__user').all()
    else:
        client = get_object_or_404(Client, user=request.user)
        from_account_queryset = Account.objects.filter(client=client)

    form = TransferForm(
        request.POST or None,
        from_account_queryset=from_account_queryset
    )
    if form.is_valid():
        from_account = form.cleaned_data['from_account']
        to_account = form.cleaned_data['to_account']
        amount = form.cleaned_data['amount']

        with db_transaction.atomic():
            from_account.balance -= amount
            to_account.balance += amount
            from_account.save()
            to_account.save()

            Transaction.objects.create(
                account=from_account,
                transaction_type='DEBIT',
                amount=amount
            )
            Transaction.objects.create(
                account=to_account,
                transaction_type='CREDIT',
                amount=amount
            )

        return redirect('dashboard')

    return render(request, 'banking/transfer_money.html', {'form': form})


@login_required
def add_client(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    form = ClientForm(request.POST or None)
    if form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password="12345678"
        )
        Client.objects.create(
            user=user,
            phone=form.cleaned_data['phone']
        )
        return redirect('add_account')

    return render(request, 'banking/add_client.html', {'form': form})


@login_required
def add_account(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    form = AccountForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'banking/add_account.html', {'form': form})


@login_required
def edit_account(request, id):
    account = get_object_or_404(Account, id=id)

    if not request.user.is_superuser:
        return redirect('dashboard')

    form = AccountForm(request.POST or None, instance=account)
    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'banking/edit_account.html', {'form': form})


@login_required
def delete_account(request, id):
    account = get_object_or_404(Account, id=id)

    if request.method == 'POST':
        account.delete()
        return redirect('dashboard')

    return render(request, 'banking/delete_account.html', {'account': account})


@login_required
def account_detail(request, id):
    account = get_object_or_404(Account, id=id)

    if not request.user.is_superuser and account.client.user != request.user:
        return redirect('dashboard')

    transactions = account.transactions.all().order_by('-date')
    selected_type = request.GET.get('type')

    credit_total = transactions.filter(transaction_type='CREDIT').aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    debit_total = transactions.filter(transaction_type='DEBIT').aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    transaction_count = transactions.count()

    if selected_type in ['CREDIT', 'DEBIT']:
        transactions = transactions.filter(transaction_type=selected_type)

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.account = account

            if transaction.transaction_type == 'DEBIT':
                account.balance -= transaction.amount
            else:
                account.balance += transaction.amount

            account.save()
            transaction.save()
            return redirect('account_detail', id=id)
    else:
        form = TransactionForm()

    return render(request, 'banking/account_detail.html', {
        'account': account,
        'transactions': transactions,
        'credit_total': credit_total,
        'debit_total': debit_total,
        'transaction_count': transaction_count,
        'selected_type': selected_type,
        'form': form,
    })


@login_required
def export_pdf(request, id):
    account = get_object_or_404(Account, id=id)

    if not request.user.is_superuser and account.client.user != request.user:
        return redirect('dashboard')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transactions.pdf"'

    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Compte: {account.account_number}")

    y = 760
    for t in account.transactions.all():
        p.drawString(100, y, f"{t.date} | {t.transaction_type} | {t.amount} MAD")
        y -= 20

    p.showPage()
    p.save()
    return response
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # إنشاء Client مرتبط بالـ User
            Client.objects.create(user=user)

            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})