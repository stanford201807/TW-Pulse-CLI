# Panduan Upload ke GitHub

Panduan lengkap untuk mengupload **Pulse CLI** ke GitHub.

**Repository:** https://github.com/sukirman1901/Pulse-CLI

## Daftar Isi

1. [Persiapan](#1-persiapan)
2. [Buat Repository GitHub](#2-buat-repository-github)
3. [Inisialisasi Git Lokal](#3-inisialisasi-git-lokal)
4. [Push ke GitHub](#4-push-ke-github)
5. [Konfigurasi Repository](#5-konfigurasi-repository)
6. [Langkah Opsional](#6-langkah-opsional)

---

## 1. Persiapan

### Pastikan File Sudah Lengkap

Struktur repository yang sudah disiapkan:

```
pulse-cli/
├── .env.example          # Template environment variables
├── .gitignore            # File yang diabaikan Git
├── CHANGELOG.md          # Riwayat perubahan
├── CONTRIBUTING.md       # Panduan kontribusi
├── LICENSE               # Lisensi MIT
├── README.md             # Dokumentasi lengkap
├── pyproject.toml        # Konfigurasi project
├── config/
│   └── pulse.yaml
├── data/
│   └── tickers.json
├── pulse/                # Source code
│   ├── __init__.py
│   ├── ai/
│   ├── cli/
│   ├── core/
│   └── utils/
└── tests/                # Test suite
```

### Pastikan Tidak Ada Secrets

Cek bahwa file sensitif tidak akan ter-commit:

```bash
# File yang HARUS ada di .gitignore:
# - .env
# - secrets.json
# - auth_state.json
# - *.pem
# - *.key
```

---

## 2. Buat Repository GitHub

### Via Website

1. Buka https://github.com/new
2. Isi informasi:
   - **Repository name**: `pulse-cli`
   - **Description**: `AI-Powered Indonesian Stock Market Analysis CLI`
   - **Visibility**: Public atau Private
   - **JANGAN** centang "Add a README file" (sudah ada)
   - **JANGAN** centang "Add .gitignore" (sudah ada)
   - **JANGAN** pilih license (sudah ada)
3. Klik **Create repository**

### Via GitHub CLI

```bash
# Install GitHub CLI jika belum
brew install gh  # macOS
# atau
sudo apt install gh  # Ubuntu

# Login ke GitHub
gh auth login

# Buat repository
gh repo create pulse-cli --public --description "AI-Powered Indonesian Stock Market Analysis CLI"
```

---

## 3. Inisialisasi Git Lokal

Buka terminal dan masuk ke direktori project:

```bash
cd /path/to/pulse-cli
```

### Jika Belum Ada Git Repository

```bash
# Inisialisasi git
git init

# Konfigurasi user (jika belum)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Tambahkan semua file
git add .

# Cek status
git status

# Commit pertama
git commit -m "Initial commit: Pulse CLI v0.1.0

- AI-powered Indonesian stock market analysis CLI
- Technical & fundamental analysis
- SAPTA pre-markup detection engine
- Trading plan generator with TP/SL/RR
- Stock screening with multiple presets
- Natural language support (ID & EN)"
```

### Jika Sudah Ada Git Repository

```bash
# Cek status
git status

# Tambahkan perubahan
git add .

# Commit
git commit -m "docs: add comprehensive documentation for GitHub release"
```

---

## 4. Push ke GitHub

### Hubungkan ke Remote Repository

```bash
# Tambahkan remote origin
git remote add origin https://github.com/sukirman1901/Pulse-CLI.git

# Atau jika menggunakan SSH
git remote add origin git@github.com:sukirman1901/Pulse-CLI.git

# Verifikasi remote
git remote -v
```

### Push ke GitHub

```bash
# Rename branch ke main (jika masih master)
git branch -M main

# Push ke GitHub
git push -u origin main
```

### Jika Menggunakan SSH dan Perlu Setup

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Tambahkan ke ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Paste di GitHub: Settings > SSH and GPG keys > New SSH key
```

---

## 5. Konfigurasi Repository

### Setelah Push, Konfigurasi di GitHub:

#### 5.1 Repository Settings

1. Buka repository di GitHub
2. Klik **Settings**

#### 5.2 About Section

Di halaman utama repository, klik ikon gear di bagian "About":
- **Description**: AI-Powered Indonesian Stock Market Analysis CLI
- **Website**: (kosongkan atau isi jika ada)
- **Topics**: `python`, `cli`, `stock-market`, `indonesia`, `idx`, `trading`, `technical-analysis`, `ai`, `machine-learning`

#### 5.3 Branches Protection (Opsional)

Settings > Branches > Add rule:
- Branch name pattern: `main`
- Require pull request reviews before merging
- Require status checks to pass

#### 5.4 Issues & Discussions

Settings > Features:
- ✅ Issues
- ✅ Discussions (opsional)

---

## 6. Langkah Opsional

### 6.1 Buat Release

```bash
# Buat tag
git tag -a v0.1.0 -m "Initial release: Pulse CLI v0.1.0"

# Push tag
git push origin v0.1.0
```

Di GitHub:
1. Klik **Releases** > **Create a new release**
2. Pilih tag `v0.1.0`
3. Title: `Pulse CLI v0.1.0 - Initial Release`
4. Description: Copy dari CHANGELOG.md
5. Klik **Publish release**

### 6.2 Setup GitHub Actions (CI/CD)

Buat file `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run linting
        run: ruff check pulse/
      
      - name: Run tests
        run: pytest --cov=pulse
```

### 6.3 Badges untuk README

Tambahkan badges di README.md setelah push:

```markdown
![Tests](https://github.com/USERNAME/pulse-cli/actions/workflows/test.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
```

---

## Checklist Sebelum Upload

- [ ] `.env` file tidak ter-commit (ada di .gitignore)
- [ ] Tidak ada API key atau password dalam code
- [ ] README.md sudah lengkap
- [ ] LICENSE file ada
- [ ] .gitignore sudah benar
- [ ] pyproject.toml sudah benar
- [ ] Semua test passing (opsional)

---

## Troubleshooting

### Error: Permission Denied

```bash
# Jika menggunakan HTTPS, pastikan credential benar
git config --global credential.helper store

# Atau gunakan Personal Access Token
# GitHub > Settings > Developer settings > Personal access tokens
```

### Error: Remote Already Exists

```bash
# Hapus remote lama
git remote remove origin

# Tambahkan ulang
git remote add origin https://github.com/USERNAME/pulse-cli.git
```

### Error: Large Files

```bash
# Jika ada file besar (>100MB), gunakan Git LFS
git lfs install
git lfs track "*.pkl"
git lfs track "*.bin"
git add .gitattributes
```

---

## Selesai!

Setelah mengikuti panduan ini, repository Anda akan tersedia di:

```
https://github.com/USERNAME/pulse-cli
```

Clone untuk testing:

```bash
git clone https://github.com/USERNAME/pulse-cli.git
cd pulse-cli
pip install -e .
pulse
```

---

*Panduan ini dibuat untuk Pulse CLI v0.1.0*
