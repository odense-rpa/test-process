# test-process

Testproces der besøger en fast liste af nyhedssites via Playwright og tæller billeder og links på hver side. Bruges til at validere det Python-baserede processtyringsværktøj bygget på Automation Server-platformen.

## Hvad gør processen?

1. Fylder arbejdskøen med 10 store nyhedssites (CNN, BBC, NYT, The Guardian, Reuters, Washington Post, Al Jazeera, Fox News, NBC News, USA Today)
2. Åbner hvert URL i en headless Chromium-browser via Playwright
3. Tæller antallet af `<img>`-tags på siden
4. Tæller antallet af `<a>`-tags med et `href`-attribut
5. Opdaterer arbejdskøen med resultatet (antal billeder og links)
6. Logger resultatet og venter 10–40 sekunder (tilfældigt) mellem hvert element
7. Markerer fejlede elementer med en fejlbesked hvis der opstår en undtagelse

## Installation

```sh
uv sync
```

## Kørsel

```sh
uv run python main.py --queue   # Fyld arbejdskøen
uv run python main.py           # Behandl arbejdskøen
```

Brug `--fail` for at udløse en `RuntimeError` med nested call stack — til test af fejl- og stack trace-rapportering i Automation Server.

## Konfiguration

| Miljøvariabel | Beskrivelse |
|---|---|
| `ATS_URL` | Base-URL til Automation Server-instansen (f.eks. `http://localhost:8000`) |
| `ATS_TOKEN` | Bearer token til autentificering mod Automation Server |
| `ATS_WORKQUEUE_OVERRIDE` | Sæt til `1` for at bruge arbejdskøen uden en aktiv Automation Server-session (til lokal test) |

## Afhængigheder

| Pakke | Formål |
|---|---|
| `automation-server-client` | Klientbibliotek til Automation Server (arbejdskø, proceslivscyklus) |
| `playwright==1.55.0` | Browserautomatisering — starter headless Chromium og skraber sideindhold |

## GDPR og sikkerhed

Processen behandler ingen personoplysninger.
