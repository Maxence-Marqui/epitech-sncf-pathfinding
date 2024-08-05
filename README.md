# T-AIA-901_LIL_1

# Introduction

This project is an end-to-end solution that allows a user to find its way between two given train station

#### Example:

John wants to go from Lille to Marseille

He inputs the following sentence into the program : 

"Je veux aller de Lille à Marseille"

He can either type it or say it into his microphone

The validity of the sentence is checked, if :
- The sentence is in French
- The sentence has a departure and an arrival location that exists

The program then finds the quickest way to get from the departure location to the desired arrival

It prints a recap of the steps between those two points

| location name          | travel time | transportation mode |
|------------------------|-------------|---------------------|
| Lille flandres         | 10min       | foot                |
| Marne La Vallee Chessy | 2H          | train               |
| ...                    | ...         | ...                 |
| Marseille              | 3h          | train               |

The program also displays a map with all the points the user will visit during his trip

## Table Of Content

- [Installation](#installation)
    - [Docker-compose](#Docker-compose)
    - [Run it locally](#Run-it-locally)
- [Astar pathfinding](#Astar)
    - [Code architecture](#Code-architecture)
    - [Database Python setup](#Database-setup)
    - [Astar-logic](#Astar-logic)
    - [Code-logic](#Code-logic)
- [NLP SpacyModel](#NLP_Spacy_Model)
- [Visualisation Streamlit](#Visualsation_Streamlit)
- [NLP voiceRecogniton](#NLP_voiceRecogniton)
    - [Jupyter notebook](#Jupyter)
    - [How it works?](#VoiceRecognization-techno-explaination)
    - [View result of the model](#Result_of_the_model)
    - [The limits of the models](#Limits_voiceRecognization)
- [The team up](#Team_up)

## Installation

The installation is a necessary step before starting the running of python project.
In this step we will explain how can we starts the database plus how run the python project

### Docker-compose

**Note:** Docker is required

First of all you need to install the database, you need to run the docker-compose in this directory

```bash
docker-compose up -d 
```

When db is installed, you could execute inside the sql file to populate the db.

### Run-it-locally

**Note:** Python is required

You need to install the requirement.txt with this command

```bash
pip install -r requirements.txt
```

When the python package installation is done you could run the main.py with 

```bash
python main.py
```

Here we are ! The project is now run 

## Astar

Astar is the algorithm used to determined the path to a destination.
He is used to predict path.

### Code-architecture

Here is a structure representation of the pathding project.

- [.env](#.env)
- [Pathfinding]
    - [Dockerfile](#Dockerfile_pathfinding)
    - [entrypoint.sh](#Entrypoint.sh)
    - [main.py](#Main.py)
    - [map_class.py](#Map_class.py)
    - [Requirement.txt](#Requirement.txt)
    - [setup_db.py](#Setup_db.py)

#### .env

The .env files contains all database information

#### Dockerfile_pathfinding

The Dockerfile is used to instantiate python in Docker and open an accees of he's utilisation.
In the end, the Dockerfile will run entrypoint.sh, which run the project. 

#### Entrypoint.sh

As I said it before, entrypoint will run the project  `main.py`

#### Main.py

Main. py is used to run the project

#### Map_class.py

Map_class is the logical class of the directory. 
He ensured the Astar algortihm and all the preprocessing before the traitment to ensure a quick prediction of the path.

#### Requirement.txt

A utilitary files makes for python installation

#### Setup_db.py

Setup_db is the entry point of the database. 
Often used for the database connection, he is also used to initialize the db.


### Database-setup

Now move on `.\pathfinding` directory.

We can find `setup_db.py`, in this file we could find some method which is globally to used to connect us to the database when we did a sql request.
We can also find the method `setup_db` used to build the database from the SNCF data given.
The rest of the page concerns some methods to verify if the db or one table exists and some typical methods to verify the data coherency.

Brief aside on some enum like `os.environ["DB_HOST"]`, these enum are related in `.env` files,
we could find inside the informations about database.

### Astar-logic

**Note:** *node : is a point refered on the map used to predict a path.

A* logic is commonly used on some project.

Brief recap about the logic of Astar.
A* has been designed to achieve an efficient pathfinding process..
For this A* has a node* loading facilitate because of a properly research of the node picken for the prediction.
Indeed in A*, we don't load all nodes just the nodes between start point and ended point and just more if necessary.

In second steps after the `nodes loading`, we will calculate the cost of the trip.
To makes this, we will used a certain formula : `F = G + H`
    - F : final cost of 2 endpoints (starts to end points)
    - G : He is the cost of 2 neighboor nodes, it depends of some parameters, distances, times to make it etc...
    - H : The heuritic distance is the Median movement distance. It is the ideal linear distance between current points and end points.

This formula is used to find the best path between 2 nodes.
Indeed, we will calculate between starting points and ended points the best paths possible.
We need to imagine bewteen starts point called S and endpoint called E some points called A,B,C,D,E.
So the idea with A* is when we starts at S, we will calculated the lowest distance between the 2 nodes plus the heuritic saw previously. 
And we will reiterate that to find the path with the lowest F value.

The global idea is to pick the distance with the smallest cost.
Now, let's talk about the code logic.

### Code-logic

I will not explain the code line by line but just globally.

The main.py will in a first time load the .env and keep in memory.
After this we will make if it's the first time a json file which contains the links between the trains stations and the eventual trips between all stations.
And after that we will go inside this file to pick the prediction previously make and pick it for the trips asked.

The code also contains the trip on foot and subway stations. To have this informations we just used google map API.

Here is the global idea of how it's works, when user said How can I go from Lille to Dunkerque.

## NLP Spacy Model

The link to the document: [NLP Spacy Model Document](./nlp/Documentation_NLP_Spacy.pdf)

## Streamlit Visualisation

The link to the document: [Streamlit Visualisation Document](./nlp/Documentation_Visualisation_Streamlit.pdf)

## Voice recognition first approach

This version is based on the CTC method, as explained in the document below.
The link to the document: [Speech Recognition Document](./voice_recognization/Speechreco.pdf) 
The link to the code: [Speech Recognition Code](./voice_recognization/speechrecognization.ipynb)

## Voice recognition second approach

This version implements javascript's native [speech recognition module](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)

The solution has been retained for the following aspects :
- Frontend execution
- Continuous recognition

## Team_up

In progress ...


