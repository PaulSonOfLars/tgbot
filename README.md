# PythonItaliaTGbot

Bot principale per il gruppo Telegram di [PythonItalia](https://t.me/python_ita).

## Che cos'è?

Questo bot è un fork della versione base di tgBot (ex Marie). Lo sviluppo orizzontale del bot ha permesso di aggiungere funzionalità e risolvere bug presenti nel codice sorgente originale.

### Il deploy

Il deploy del bot può essere effettuato su Heroku (settando le variabili di ambiente) che su una VPS dedicata (preferibilmente con kernel linux > 2.6.13).

### Configurazione del db

Il primo step necessario è la configurazione del database postgres.

#### Installazione e configurazione di postgres
- Installa postgres:

```
sudo apt-get update && sudo apt-get install postgresql
```

- Cambia l'utente postgres:

```
sudo su - postgres
```

- Crea un nuovo database utente (cambia USER con il nome dell'utente):

```
createuser -P -s -e USER
```
Ti verrà chiesto di inserire una password.

- Crea una nuova tabella nel db:

```
createdb -O USER YDB_NAME
```
- In fine

```
psql DB_NAME -h YOUR_HOST USER
```
A questo punto sarai in grado di connetterti al db via terminal. Di default YOUR_HOST dovrebbe essere 0.0.0.0:5432.
Il database-uri sarà quindi:
```
postgres://username:pw@hostname:port/db_name
```


## Configurazione

Esistono due modi per configurare il bot: modificando il file config.py oppure impostando delle variabili d'ambiente.

Il metodo migliore è l'uso del file config.py perchè è più semplice rivedere tutte le impostazioni in un singolo file.
Il metodo predefinito per creare il file config.py è estendere la classe di sample_config.

Un esempio di config.py potrebbe essere:

```
from tg_bot.sample_config import Config


class Development(Config):
    OWNER_ID = 00000000  # my telegram ID
    OWNER_USERNAME = "########"  # my telegram username
    API_KEY = "your bot api key"  # my api key, as provided by the botfather
    SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost:5432/database'  # sample db credentials
    MESSAGE_DUMP = '00000000' # some group chat that your bot is a member of
    USE_MESSAGE_DUMP = True
    SUDO_USERS = [0000000, 000000]  # List of id's for users which have sudo access to the bot.
    LOAD = []
    NO_LOAD = ['translation']
```

Nel caso in cui tu voglia deployare il bot su heroku dovrai impostare le ENV. Sono supportate le seguenti variabili:



    ENV: Setting this to ANYTHING will enable env variables

    TOKEN: Your bot token, as a string.

    OWNER_ID: An integer of consisting of your owner ID

    OWNER_USERNAME: Your username

    DATABASE_URL: Your database URL

    MESSAGE_DUMP: optional: a chat where your replied saved messages are stored, to stop people deleting their old

    LOAD: Space separated list of modules you would like to load

    NO_LOAD: Space separated list of modules you would like NOT to load

    WEBHOOK: Setting this to ANYTHING will enable webhooks when in env mode messages

    URL: The URL your webhook should connect to (only needed for webhook mode)

    SUDO_USERS: A space separated list of user_ids which should be considered sudo users

    SUPPORT_USERS: A space separated list of user_ids which should be considered support users (can gban/ungban, nothing else)

    WHITELIST_USERS: A space separated list of user_ids which should be considered whitelisted - they can't be banned.

    DONATION_LINK: Optional: link where you would like to receive donations.

    CERT_PATH: Path to your webhook certificate

    PORT: Port to use for your webhooks

    DEL_CMDS: Whether to delete commands from users which don't have rights to use that command

    STRICT_GBAN: Enforce gbans across new groups as well as old groups. When a gbanned user talks, he will be banned.

    WORKERS: Number of threads to use. 8 is the recommended (and default) amount, but your experience may vary. Note that going crazy with more threads wont necessarily speed up your bot, given the large amount of sql data accesses, and the way python asynchronous calls work.

    BAN_STICKER: Which sticker to use when banning people.

    ALLOW_EXCL: Whether to allow using exclamation marks ! for commands as well as /.



### Dependency

Installa le dependency con questo comando:

```
pip3 install -r requirements.txt
```

## Moduli

#### Imposta l'ordine di caricamento dei moduli

L'ordine di caricamento in memoria dei moduli può essere opportunamente modificato tramite l'uso di LOAD e NO_LOAD.

Nota: NO_LOAD è prioritario rispetto a LOAD

## Avviare il bot con docker

#### Requisiti
- docker
- docker-compose

#### Avvio
- Crea un file .env usando docker/dev/config.sample come template e salvandola in docker/dev/
- Assicurati di essere nella root del progetto e inserisci il seguente comando: 
```
docker-compose -f docker/dev/docker-compose.yml up -d
```

## Costruito con

* [tgbot](https://github.com/PaulSonOfLars/tgbot) - Bot modulare scritto in Python3
* [Trevis CI](https://travis-ci.com) - Deploy in production
* [Docker](https://www.docker.com/) - Used to generate RSS Feeds

## Come contribuire

Per favore leggi [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) per avere dettagli sulle regole
per contribuire e come effettuare una pull-request.

## Versioning

Noi usiamo [SemVer](http://semver.org/) per il versioning, sincronizzato con i tag in production di GH.

## Autori

Controlla la lista di [contributors](https://github.com/Kavuti/python-italy-telegram-bot/graphs/contributors) che hanno reso questo progetto grande.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

