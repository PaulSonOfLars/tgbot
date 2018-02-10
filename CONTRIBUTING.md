# Contributing

Contributions are very welcome! Here are some guidelines on how the project is designed.

### CodeStyle

- Adhere to PEP8 as much as possible.

- Line lengths should be under 120 characters, use list comprehensions over map/filter, don't leave trailing whitespace.

- More complex pieces of code should be commented for future reference.

### Structure

There are a few self-imposed rules on the project structure, to keep the project as tidy as possible.
- All modules should go into the `modules/` directory.
- Any database accesses should be done in `modules/sql/` - no instances of SESSION should be imported anywhere else.
- Make sure your database sessions are properly scoped! Always close them properly.
- When creating a new module, there should be as few changes to other files as possible required to incorporate it.
Removing the module file should result in a bot which is still in perfect working condition.
- If a module is dependent on multiple other files, which might not be loaded, then create a list of at module
load time, in `__main__`, by looking at attributes. This is how migration, /help, /stats, /info, and many other things
are based off of. It allows the bot to work fine with the LOAD and NO_LOAD configurations.
- Keep in mind that some things might clash; eg a regex handler could clash with a command handler - in this case, you 
should put them in different dispatcher groups.

Might seem complicated, but it'll make sense when you get into it. Feel free to ask me for a hand/advice!
