# 🦖 DinoBot – AI Virtual Assistant

DinoBot is a desktop virtual assistant that chats in Spanish. It reads the user's message, detects the topic with natural language processing, and routes it to a specialized module. It was built as a team project for the **Artificial Intelligence** course at the School of Engineering, UNAM (November 2025).

This repository is my portfolio version of the project, with bug fixes and performance improvements made after the course.

## Features

- **Topic classifier (NLP):** decides whether a message is about the subway, music, health or general chat, combining semantic similarity (spaCy) with keywords.
- **Mexico City Metro route planner:** models the subway network as a weighted graph and finds the best route with **A\* search**, including transfers and estimated travel time.
- **Mood-based music recommender:** represents songs as energy/valence vectors, interprets the user's mood (including negations such as "nothing sad") and recommends the closest songs.
- **Medical expert system:** detects symptoms in free text, ignores negated ones ("I don't have a fever") and ranks the most likely conditions. It is an educational tool and does not replace a medical consultation.
- **General chat:** greetings, questions about AI, and the current date and time.
- **Chat-style desktop interface** built with Flet.

## My contribution

I focused on the **music recommender** and the **medical expert system**. For this portfolio version I also:

- Fixed the ordering of diagnoses in the medical module.
- Fixed station name detection in the route planner.
- Improved the music recommender by switching from cosine similarity to Euclidean distance.
- Reduced response time with caching.
- Added an automatic installation script for Windows.

## Tech stack

Python · spaCy · NLTK · scikit-learn · pandas · NumPy · Flet · JSON knowledge bases

## Getting started

```bash
pip install -r requirements.txt
python -m spacy download es_core_news_md
python -c "import nltk; [nltk.download(x) for x in ('punkt', 'punkt_tab', 'stopwords')]"
python main.py
```

On Windows, just double-click `iniciar.bat`: it creates a virtual environment, installs the dependencies, the spaCy Spanish model and the NLTK data the first time, and then launches the app.

## Project structure

| File | Responsibility |
|---|---|
| `main.py` | Chat interface (Flet) |
| `tokenizacion.py`, `analisis.py` | Text preprocessing and topic classification |
| `metro.py`, `grafos.py` | Metro graph and A\* route search |
| `vetores_musica.py` | Music recommender |
| `inferencia.py` | Medical expert system |
| `kb/` | Knowledge bases in JSON |
| `iniciar.bat` | One-click setup and launch on Windows |

## Credits

Original project by team **Ingesaurios** for the Artificial Intelligence course (UNAM):
[JysusAle/asistente-virtual-ia](https://github.com/JysusAle/asistente-virtual-ia).
