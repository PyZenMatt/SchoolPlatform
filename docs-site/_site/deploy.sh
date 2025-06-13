#!/bin/bash

# Script per il deploy del sito Jekyll su GitHub Pages

echo "🚀 Iniziando il deploy del sito Jekyll..."

# Controlla se siamo nella directory corretta
if [ ! -f "_config.yml" ]; then
    echo "❌ Errore: _config.yml non trovato. Assicurati di essere nella directory docs-site/"
    exit 1
fi

# Installa le dipendenze se necessario
if [ ! -d "_site" ]; then
    echo "📦 Installando dipendenze Jekyll..."
    bundle install
fi

# Build del sito
echo "🔨 Building del sito Jekyll..."
bundle exec jekyll build

# Controlla se il build è andato a buon fine
if [ $? -eq 0 ]; then
    echo "✅ Build completato con successo!"
    echo "📁 Il sito è pronto nella cartella _site/"
    echo ""
    echo "📋 Prossimi passi per il deploy su GitHub Pages:"
    echo "1. Crea un nuovo repository su GitHub chiamato 'tuousername.github.io'"
    echo "2. Inizializza git in questa directory: git init"
    echo "3. Aggiungi i file: git add ."
    echo "4. Fai il primo commit: git commit -m 'Initial Jekyll site'"
    echo "5. Collega al repository: git remote add origin https://github.com/tuousername/tuousername.github.io.git"
    echo "6. Push su GitHub: git push -u origin main"
    echo ""
    echo "🌐 Il sito sarà disponibile su: https://tuousername.github.io"
else
    echo "❌ Errore durante il build. Controlla i messaggi di errore sopra."
    exit 1
fi
