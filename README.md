# MarketWatch — Bot notifiche annunci (Subito/Vinted)

Monitora ricerche su Vinted e Subito, ti notifica su Telegram appena esce
qualcosa di nuovo. Girato 24/7 gratis su GitHub Actions.

⚠️ **Nota onesta**: Subito blocca spesso il traffico dai server cloud
(datacenter IP). Vinted di solito funziona con la tecnica usata qui, ma
non è garantito al 100% nel tempo — questi siti cambiano le protezioni
senza preavviso. Se Subito smette di dare risultati, usa il "Salva ricerca"
nativo dell'app Subito come rete di sicurezza.

## Setup (10-15 minuti, una tantum)

### 1. Crea il bot Telegram
1. Apri Telegram, cerca **@BotFather**
2. Manda `/newbot`, segui le istruzioni, scegli un nome
3. Ti darà un **token** tipo `123456:ABC-DEF...` → salvalo
4. Cerca **@userinfobot** su Telegram, avvialo: ti dà il tuo **Chat ID** (un numero) → salvalo
5. Apri una chat col tuo bot appena creato e manda un messaggio qualsiasi (serve per "sbloccarlo")

### 2. Crea il repository GitHub
1. Vai su [github.com/new](https://github.com/new), crea un repo (es. `marketwatch`), **privato** consigliato
2. Carica tutti i file di questo pacchetto nel repo (via web: "Add file" → "Upload files", trascina tutto mantenendo le cartelle)

### 3. Aggiungi i secrets per Telegram
Nel repo: **Settings → Secrets and variables → Actions → New repository secret**
- `TELEGRAM_BOT_TOKEN` → il token di BotFather
- `TELEGRAM_CHAT_ID` → il tuo chat ID

### 4. Attiva GitHub Pages (per il pannello)
**Settings → Pages → Source: Deploy from branch → main → / (root) → Save**
Dopo 1-2 minuti il pannello sarà visibile a:
`https://TUOUTENTE.github.io/marketwatch/`

### 5. Crea un Personal Access Token (per far scrivere il pannello sul repo)
1. Vai su [github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta)
2. **Generate new token** → Fine-grained token
3. Repository access → seleziona solo `marketwatch`
4. Permissions → **Contents: Read and write**
5. Genera e copia il token (inizia con `github_pat_...`)

### 6. Apri il pannello dal telefono
Vai su `https://TUOUTENTE.github.io/marketwatch/`, inserisci:
- Repo: `tuoutente/marketwatch`
- Token: quello appena creato

Salva, poi aggiungi le tue ricerche. Da questo momento lo script su
GitHub Actions (che gira ogni ~10 minuti, gratis) le controllerà e ti
manderà un messaggio Telegram per ogni nuovo annuncio.

## Test manuale
Nel repo → tab **Actions** → "MarketWatch Check" → **Run workflow**,
per testare subito senza aspettare i 10 minuti.

## Limiti da sapere
- GitHub Actions gratis: 2000 minuti/mese sui repo privati (più che sufficiente per un check ogni 10 min)
- Il cron di GitHub può ritardare di qualche minuto in certi orari, non è millisecond-precise
- Se Subito o Vinted cambiano le loro protezioni anti-bot, lo script potrebbe smettere di funzionare e serve aggiornarlo
