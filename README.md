# Dashboard de supervision - Frontend Nuxt / Vue

## Description

Application frontend développée avec **Nuxt 3**, **Vue 3**, **TypeScript** et **Leaflet** pour afficher des données géolocalisées sur une carte.

Le projet permet de :

- afficher une carte interactive
- afficher des points sous forme de cercles
- afficher un indice dans chaque cercle
- colorer les cercles selon la valeur de l’indice
- ouvrir une popup au clic avec les informations complémentaires
- filtrer les données par recherche, zone, dates et bornes d’indice
- afficher des indicateurs de synthèse
- afficher une répartition des indices
- afficher une évolution temporelle

## Contexte fonctionnel

Le frontend **n’interagit qu’avec le backend**.

Le backend est responsable de :

- récupérer les données fournies par l’équipe data
- alimenter une base de données
- initialiser la base avec les données des 10 derniers jours
- mettre à jour les données plusieurs fois par jour
- exposer un endpoint filtrable pour le frontend

Le frontend est responsable de :

- appeler le backend
- afficher les données sur la carte
- proposer les filtres utilisateur
- afficher les statistiques et visualisations associées

## Stack technique

- **Nuxt 3**
- **Vue 3**
- **TypeScript**
- **Leaflet**

## Installation

```bash

npm install
npm install leaflet
npm install -D @types/leaflet
npm run dev