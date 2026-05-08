from django import forms
from django.contrib.auth.models import User
from .models import Account, Transaction, Client

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['client', 'account_number', 'balance']


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount']


class TransferForm(forms.Form):
    from_account = forms.ModelChoiceField(queryset=Account.objects.all(), label="Compte source")
    to_account_number = forms.CharField(max_length=20, label="Compte destinataire")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1, label="Montant")

    def __init__(self, *args, from_account_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if from_account_queryset is not None:
            self.fields['from_account'].queryset = from_account_queryset

    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get('from_account')
        to_account_number = cleaned_data.get('to_account_number')
        amount = cleaned_data.get('amount')
        to_account = None

        if to_account_number:
            try:
                to_account = Account.objects.get(account_number=to_account_number.strip())
            except Account.DoesNotExist:
                raise forms.ValidationError("Compte destinataire introuvable.")

            cleaned_data['to_account'] = to_account

        if from_account and to_account and from_account.id == to_account.id:
            raise forms.ValidationError("Vous ne pouvez pas envoyer de l’argent vers le même compte.")

        if from_account and amount and from_account.balance < amount:
            raise forms.ValidationError("Solde insuffisant pour effectuer ce transfert.")

        return cleaned_data


class ClientForm(forms.Form):
    username = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=20, required=False)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        return username
