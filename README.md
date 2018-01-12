# tgbot
A modular telegram Python bot running on python3 with an sqlalchemy database.

Originally a simple group management bot with multiple admin features, it has evolved, becoming extremely modular and 
simple to use.

Can be found on telegram as [Marie](https://t.me/BanhammerMarie_bot).
Alternatively, [find me on telegram](https://t.me/SonOfLars) for any help/questions!

## Setting up the bot (Read this before trying to use!):
Please make sure to use python3.6, as I cannot guarantee everything will work as expected on older python versions!
This is because markdown parsing is done by iterating through a dict, which are ordered by default in 3.6.

### config.py

Make sure you have a config.py file in your tg_bot folder. This is where your bot token will be loaded from, as well 
as your database URI (if you're using a database).
Have a look at sample_config.py for an idea of what it must contain.

It is recommended to import sample_config and extend the Config class, as this will ensure your config contains all 
defaults set in the sample_config.

If you can't have a config.py file, it is also possible to use environment variables - see `./tg_bot/__init__.py` for 
a list of possible ENV variables.

### Python dependencies

Install the necessary python dependencies by moving to the project directory and running:

`pip3 install -r requirements.txt`.

This will install all necessary python packages.

### Database

If you wish to use a database-dependent module (eg: locks, notes, userinfo, users, filters, welcomes),
you'll need to have a database installed on your system. I use postgres, so I recommend using it for optimal compatibility.

In the case of postgres, this is how you would set up a the database on a debian/ubuntu system. Other distributions may vary.

- install postgresql:

`sudo apt-get update && sudo apt-get install postgresql`

- change to the postgres user:

`sudo su - postgres`

- create a new database user (change YOUR_USER appropriately):

`createuser -P -s -e YOUR_USER`

This will be followed by you needing to input your password.

- create a new database table:

`createdb -O YOUR_USER YOUR_DB_NAME`

Change YOUR_USER and YOUR_DB_NAME appropriately.

- finally:

`psql YOUR_DB_NAME -h YOUR_HOST YOUR_USER`

This will allow you to connect to your database via your terminal.
By default, YOUR_HOST should be 0.0.0.0:5432.

### Starting the bot.

To start the bot, simply run:

`python3 -m tg_bot`

## Modules
### Setting load order.

The module load order can be changed via `modules/load.json`.
The file should contain ONLY one json object.
Two variables are looked for:
- `load`: a list of elements to load, and in which order to load them.
- `no_load`: a list of elements NOT to load.

If `load` is not present, or is an empty list, all modules in `modules/` will be selected for loading by default.

If `no_load` is not present, or is an empty list, all modules selected for loading will be loaded.

If a module is in both `load` and `no_load`, the module will not be loaded - `no_load` takes priority.
### Creating your own modules.

Creating a module has been simplified as much as possible - but do not hesitate to suggest more ways of simplifying.

All that is needed is that your .py file be in the modules folder.

To add commands, make sure to import the dispatcher via

`from tg_bot import dispatcher`.

You can then add commands using the usual

`dispatcher.add_handler()`.

Assigning the `__help__` variable to a string describing this modules' available
commands will allow the bot to load it and add the documentation for
your module to the /help command.

The `__migrate__()` function is used for migrating chats - when a chat is upgraded to a supergroup, the ID changes, so 
it is necessary to migrate it in the db.

The `__stats__()` function is for retrieving module statistics, eg number of users, number of chats.
