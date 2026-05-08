# DevOps Django Bank

[![CI/CD](https://github.com/Hasanpiker5543/devops/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Hasanpiker5543/devops/actions/workflows/ci-cd.yml)

Mini-projet DevOps basé sur une application de gestion bancaire avec login, client dashboard, admin dashboard, comptes, transferts et transactions.

## Auteur

El-Mehdi Taoufik

## DevOps

- Dockerfile
- docker-compose.yml
- GitHub Actions CI/CD
- Tests automatisés
- README
- Rapport PDF

## Lancement local

```powershell
pip install -r requirements.txt
cd bank
python manage.py migrate
python manage.py runserver
```

## Docker

```powershell
docker compose up --build
```

## Tests

```powershell
cd bank
python manage.py test
```

## Image Docker

```text
ghcr.io/Hasanpiker5543/devops-django-bank:latest
```
