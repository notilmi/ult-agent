# Knowledge Base Ingestion Guide

This document describes how to curate, format, and ingest official procedure documents into the **NeonDB (`pgvector`)** vector store for the ULT Polsri AI Service Agent.

---

## 1. Supported Document Types

The standalone ingestion tool (`scripts/ingest.py`) accepts two document formats:

1. **Curated Markdown Files (`.md`)**: Best for structured procedure entries with explicit metadata.
2. **Official PDF Files (`.pdf`)**: Best for raw Standard Operating Procedure (SOP) manuals, decrees (Surat Keputusan), or circulars.

---

## 2. Markdown File Format (Curated Entries)

Place Markdown files under `data/markdown/`. Each file should contain a YAML frontmatter header conforming to the PRD Section 10 specification:

```markdown
---
id: FAQ-01-001
category: academic
title: Pengajuan Surat Keterangan Mahasiswa Aktif
responsible_unit: Bagian Akademik & Unit Layanan Terpadu
form_url: https://polsri.ac.id/layanan/formulir-mahasiswa-aktif
source_title: SOP Pelayanan Administrasi Akademik Politeknik Negeri Sriwijaya 2025
source_ref: SOP/POLSRI/AKAD-001/2025
verified_at: 2026-10-15
status: published
version: 1
---

## Deskripsi Layanan
Penjelasan ringkas tentang tujuan penerbitan dokumen...

## Persyaratan
1. Kartu Tanda Mahasiswa (KTM) yang masih berlaku.
2. Bukti pembayaran UKT semester berjalan.
3. Formulir permohonan yang telah diisi lengkap.

## Prosedur dan Alur Pengajuan
1. Mahasiswa mengunduh formulir...
2. Meminta tanda tangan Ketua Jurusan...
3. Menyerahkan berkas ke loket ULT...
```

### Frontmatter Fields

| Field | Type | Description |
|---|---|---|
| `id` | String | Unique entry code (e.g. `FAQ-01-001` for Academic, `FAQ-02-001` for Student Affairs) |
| `category` | Enum | One of: `academic`, `student_affairs`, `general_admin`, `unit_info`, `complaints` |
| `title` | String | Procedure or service name |
| `responsible_unit` | String | University unit handling the service |
| `form_url` | URL | Official link to the downloadable form or portal |
| `source_title` | String | Title of the official regulation or SOP document |
| `source_ref` | String | Official SK number or regulatory reference code |
| `verified_at` | Date | Date when content was last audited by a ULT officer |
| `status` | Enum | `published`, `draft`, `in_review`, or `archived` (only `published` is retrievable) |

---

## 3. PDF Ingestion

Place PDF manuals and regulations in `data/pdf/`.
The ingestion tool will automatically:
1. Extract text page by page using `pypdf`.
2. Break long texts into semantically coherent chunks (~500 tokens with 60-token overlap).
3. Associate page numbers and document titles with each chunk.

---

## 4. Running the Ingestion CLI

Run the ingestion tool using `uv run python scripts/ingest.py`:

### Ingest All Files (Markdown and PDF) with Database Initialization
```bash
uv run python scripts/ingest.py --init-db
```

### Ingest a Specific File
```bash
uv run python scripts/ingest.py --path data/markdown/FAQ-01-001.md
```

### Ingest a Specific Directory with an Overriding Category
```bash
uv run python scripts/ingest.py --path data/pdf/ --category academic
```

### Command-line Arguments

| Argument | Default | Description |
|---|---|---|
| `--path` | `agent/data` | Path to a single file or directory to process |
| `--category` | `academic` | Default category applied to PDFs or unclassified files |
| `--init-db` | `false` | Runs `scripts/init_db.sql` on NeonDB before ingestion |
