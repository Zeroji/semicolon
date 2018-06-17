## Installation

### Which version to choose

If you want to have a copy of `;;` for yourself to run on your own server,
it's recommended you download a *stable release*, see for example the
[latest release](https://github.com/Zeroji/semicolon/tag/latest).

If you'd rather have the latest update, no matter the possible bugs, and you
like to tinker around and play with the new stuff, you'll prefer the
[direct Github link](https://github.com/Zeroji/semicolon), aka dev version.

### Requirements

- Python 3.6 (a virtual environment is recommended)
- PIP for Python
- A Discord account and a [Discord bot token](https://discordapp.com/developers/applications/me)

> If you are using Microsoft Windows, `;;` *should* work but there is no
> active effort towards the support of it. Reported issues will be taken
> care of, but with a low priority level.

### Downloading the code

To get the source code, you can either download it from Github or use
`git` to clone it locally (this is the recommended way).

- Download the [latest stable build](https://github.com/Zeroji/semicolon/releases/latest)
  (just click the "Download ZIP" button)
- Download the [latest source code](https://github.com/Zeroji/semicolon/archive/master.zip)
- Clone a specific version: `git clone --branch v0.1.0 https://github.com/Zeroji/semicolon.git`
- Clone the latest version: `git clone https://github.com/Zeroji/semicolon.git`

### Installation

Start by navigating to the directory where you downloaded the source code.

Install the required Python packages:
`pip install -r requirements`

### Required files

You'll need to create a `data` folder to store some required information.

> You can edit the `config.yaml` file to change all the paths, folder and
> file names listed in this section. If you are on Windows, make sure you
> don't accidentally save files as `file.txt` instead of just `file`.

Inside the `data` folder, create the following folder and files:

- The `secret` folder will contain your bot token, and should contain your
  API keys & related data, if any.

- Write your bot token into the `token` file inside the `secret` folder

- Write your own Discord user ID (Snowflake) inside the `master` file

- If you want people to have admin rights over `;;`, put their IDs in the
  `admin` file, separated by newlines. Your own ID should be in there.
  
- If you want `;;` to completely ignore some users, put their IDs in the
  `banned` file, separated by newlines.
  
### Running `;;`

Assuming you have done everything correctly, you should be able to run the
bot by simply typing `python core.py` from the `semicolon` folder.

If you are on a standard Linux system, with a proper Python install, you can
simply type `./core.py` to run it.

Depending on your computer and Internet connection, it might take up to 15
or 20 seconds to start the bot, if it takes longer you can check the log
file and look for errors.
