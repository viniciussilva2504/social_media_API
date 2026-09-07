<#
.SYNOPSIS
    Atalhos para levantar o ant.social localmente (Windows / PowerShell).

.DESCRIPTION
    Envolve os comandos do README numa unica interface, para nao ter de
    decorar venv/pip/env vars ou docker compose toda vez.

.USAGE
    .\dev.ps1 setup       # cria .venv, instala deps, aplica migrations (1a vez)
    .\dev.ps1 run         # runserver local (SQLite, sem Docker)
    .\dev.ps1 docker      # sobe stack completa via Docker Compose (Postgres+Redis)
    .\dev.ps1 docker-stop # docker compose down
    .\dev.ps1 migrate     # aplica migrations (venv local)
    .\dev.ps1 superuser   # cria superuser (venv local)
    .\dev.ps1 test        # roda testes (venv local)
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "run", "docker", "docker-stop", "migrate", "superuser", "test")]
    [string]$Command = "run"
)

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

function Ensure-Venv {
    if (-not (Test-Path $venvPython)) {
        Write-Host "Ambiente .venv nao encontrado. Rode '.\dev.ps1 setup' primeiro." -ForegroundColor Yellow
        exit 1
    }
}

function Set-LocalEnv {
    # Modo SQLite local: sem SQL_ENGINE cai em sqlite3, sem SECRET_KEY usa a dev key (DEBUG=1).
    $env:DEBUG = "1"
    $env:DJANGO_ALLOWED_HOSTS = "localhost 127.0.0.1"
}

switch ($Command) {
    "setup" {
        Write-Host "==> Criando .venv" -ForegroundColor Cyan
        python -m venv .venv
        Write-Host "==> Instalando dependencias" -ForegroundColor Cyan
        & $venvPython -m pip install --upgrade pip
        & $venvPython -m pip install -r requirements.txt
        Set-LocalEnv
        Write-Host "==> Aplicando migrations" -ForegroundColor Cyan
        & $venvPython manage.py migrate
        Write-Host "`nPronto! Use '.\dev.ps1 run' para subir o servidor." -ForegroundColor Green
    }
    "run" {
        Ensure-Venv
        Set-LocalEnv
        Write-Host "==> http://127.0.0.1:8000/" -ForegroundColor Green
        & $venvPython manage.py runserver
    }
    "migrate" {
        Ensure-Venv
        Set-LocalEnv
        & $venvPython manage.py migrate
    }
    "superuser" {
        Ensure-Venv
        Set-LocalEnv
        & $venvPython manage.py createsuperuser
    }
    "test" {
        Ensure-Venv
        Set-LocalEnv
        & $venvPython manage.py test
    }
    "docker" {
        Write-Host "==> Subindo stack via Docker Compose (Postgres + Redis)" -ForegroundColor Cyan
        docker compose build
        docker compose up -d
        docker compose exec web python manage.py migrate
        Write-Host "==> http://127.0.0.1:8000/" -ForegroundColor Green
    }
    "docker-stop" {
        docker compose down
    }
}
