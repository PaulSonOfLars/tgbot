# tgbot
A modular telegram Python bot running on python3 with an sqlalchemy database.

Originally a simple group management bot with multiple admin features, it has now become extremely modular and simple to use.

Can be found on telegram as [Marie](https://t.me/BanhammerMarie_bot).
Alternatively, [find me on telegram](https://t.me/SonOfLars) for any help/questions about this bot!

## Setting up the bot (Read this before trying to use!):
Please make sure you have python3 installed, as I cannot guarantee everything will work as expected with python2!

### config.py

Make sure you have a config.py file in your tg_bot folder. This is where your bot token will be loaded from, as well as your databse URI (if you're using a database).
Have a look at sample_config.py for an idea of what it must contain.

### Python dependencies

Install the necessary python dependencies by moving to the project directory and running:

`pip3 install -r requirements.txt`.

This will install all necessary python packages.

### Database

If you wish to use a database-dependent module (eg: locks, notes, userinfo, finance),
you'll need to have a database installed on your system. I use postgres, but other
databases should be compatible, as I don't use any postgres-specific types.

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
