# Integracao PHVCL — WhatsMetaClient + WhatsMetaUi (N6)

**Revisao:** 23/09/2026

## Arquivos
| Arquivo | Papel | Status |
|---------|-------|--------|
| `WhatsMetaClient.h` / `.cpp` | HTTP Indy + FetchStatus | Feito CP1252 |
| `WhatsMetaUi.h` / `.cpp` | Status / Abrir painel / botoes Preview | Feito CP1252 |
| `SenWA.cpp` | Meta antes do Whats.exe | Feito |
| `Preview.cpp` | `WhatsMetaInstalarBotoesPreview` no FormShow | Feito |
| `PH.cpp` | USEUNIT Client + Ui | Feito |
| `PH.bpk` | WhatsMetaClient.obj + WhatsMetaUi.obj | Feito |

## Botoes no Preview
Ao abrir Preview: botoes **Meta** (status) e **Painel** (ticket + browser) ao lado de SpeedButton6 (Whats).

## Encoding
CP1252 + CRLF. Usar scripts `scripts/write_whatsmeta_ui_cp1252.py` / patches se precisar reeditar.

## Build BCB5 (voce)
1. Abrir `PH.bpk`
2. Rebuild PH
3. Rebuild GEPH
4. Testar: Preview → Meta / Painel / Whats (SenWA)

## Runtime
`{PHSFTW}\WHATSPH\.env` com `PH_API_KEY`; servico na :8765
