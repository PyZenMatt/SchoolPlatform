# README per il Sito Jekyll di TeoArt School Platform

## Descrizione
Questo è il sito di documentazione per la TeoArt School Platform, costruito con Jekyll per essere hostato gratuitamente su GitHub Pages.

## Struttura del Progetto

```
docs-site/
├── _config.yml          # Configurazione Jekyll
├── _layouts/             # Template layout
│   ├── default.html      # Layout principale
│   └── page.html         # Layout per pagine
├── assets/
│   ├── css/
│   │   └── main.scss     # Stili personalizzati
│   ├── js/
│   │   └── main.js       # JavaScript personalizzato
│   └── images/           # Immagini del sito
├── index.md              # Homepage
├── features.md           # Pagina funzionalità
├── technology.md         # Pagina tecnologie
├── demo.md               # Pagina demo
├── contact.md            # Pagina contatti
├── Gemfile               # Dipendenze Ruby
└── README.md             # Questo file
```

## Setup Locale

### Prerequisiti
- Ruby (versione 2.7 o superiore)
- Bundler

### Installazione
```bash
# Installa le dipendenze
bundle install

# Avvia il server di sviluppo
bundle exec jekyll serve

# Il sito sarà disponibile su http://localhost:4000
```

## 🚀 **DEPLOY SU GITHUB PAGES - ISTRUZIONI AGGIORNATE**

### ⚠️ **PROBLEMA RISOLTO**
Se il sito mostra solo testo senza CSS e i link non funzionano:

### 1. **Configurazione Corretta**
Nel file `_config.yml`, aggiorna con i tuoi dati reali:
```yaml
baseurl: "/school"  # o il nome del tuo repository
url: "https://PyZenMatt.github.io"  # il tuo username GitHub
```

### 2. **GitHub Actions (Raccomandato)**
- Vai su GitHub → Settings → Pages
- Source: **GitHub Actions** (non "Deploy from branch")
- Il file `.github/workflows/jekyll.yml` è già configurato

### 3. **Problemi Risolti**
✅ Theme minima rimosso (causava conflitti)  
✅ Import SCSS corretti  
✅ Gemfile aggiornato per GitHub Pages  
✅ Build testato localmente  

### 4. **URL Finale**
Il sito sarà disponibile su:
```
https://PyZenMatt.github.io/school/
```

## Personalizzazione

### Configurazione
Modifica `_config.yml` per personalizzare:
- Titolo del sito
- Descrizione
- URL base
- Link social
- Menu di navigazione

### Contenuti
- **Homepage**: Modifica `index.md`
- **Funzionalità**: Modifica `features.md`
- **Tecnologie**: Modifica `technology.md`
- **Demo**: Modifica `demo.md`
- **Contatti**: Modifica `contact.md`

### Stili
Modifica `assets/css/main.scss` per personalizzare:
- Colori del brand
- Typography
- Layout responsive
- Animazioni

### Immagini
Aggiungi le tue immagini in `assets/images/`:
- `logo.png` - Logo del sito
- `favicon.ico` - Icona del browser
- `platform-dashboard.png` - Screenshot della dashboard
- `hero-background.jpg` - Immagine hero
- Altri asset grafici

## Funzionalità Incluse

### Design
- ✅ Design responsive (mobile-first)
- ✅ Dark mode support
- ✅ Animazioni CSS moderne
- ✅ Gradients e effetti visivi
- ✅ Typography ottimizzata

### Componenti
- ✅ Hero section con CTA
- ✅ Feature cards animate
- ✅ Tech stack showcase
- ✅ Demo interattive (placeholder)
- ✅ Form di contatto
- ✅ FAQ section
- ✅ Footer completo

### Performance
- ✅ CSS/JS minificati
- ✅ Immagini ottimizzate
- ✅ Font web ottimizzati
- ✅ Lazy loading
- ✅ SEO ottimizzato

### Integrations
- ✅ Bootstrap 5
- ✅ Font Awesome icons
- ✅ Jekyll SEO tag
- ✅ Jekyll sitemap
- ✅ Jekyll feed
- ✅ Google Analytics ready

## Customizzazione Avanzata

### Aggiungere Nuove Pagine
1. Crea un nuovo file `.md` nella root
2. Aggiungi il front matter YAML:
```yaml
---
layout: page
title: "Titolo Pagina"
description: "Descrizione per SEO"
---
```
3. Aggiungi il link nel menu modificando `_config.yml`

### Aggiungere Blog
1. Crea la cartella `_posts/`
2. Aggiungi post con formato `YYYY-MM-DD-title.md`
3. Crea la pagina blog/index.md

### Integrazioni Esterne
- **Google Analytics**: Aggiungi il tracking ID in `_config.yml`
- **Contact Forms**: Integra con Netlify Forms o Formspree
- **Newsletter**: Integra con Mailchimp o ConvertKit
- **Chat**: Aggiungi widget Intercom o Crisp

## Best Practices

### SEO
- ✅ Meta tags ottimizzati
- ✅ Structured data
- ✅ Sitemap XML
- ✅ RSS feed
- ✅ URL friendly

### Performance
- ✅ Minificazione CSS/JS
- ✅ Ottimizzazione immagini
- ✅ Caching headers
- ✅ CDN ready

### Accessibilità
- ✅ Semantic HTML
- ✅ Alt text per immagini
- ✅ Contrast ratio conforme
- ✅ Keyboard navigation

## Licenza
Questo template è rilasciato sotto licenza MIT. Puoi usarlo liberamente per i tuoi progetti.

## Supporto
Per domande o problemi, contatta il team di sviluppo all'indirizzo: dev@teoart.it
