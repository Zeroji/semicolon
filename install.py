#!/usr/bin/env python
"""Small installer to create default files."""
import os.path


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

print('This installer will create the default files and folders required')
print('First of all, please enter your bot token:')
token = input('Token: ')
print("Now, enter the owner's Discord ID")
owner = input('ID: ')

mkdir('config')
mkdir('data')
mkdir('data/secret')
mkdir('data/servers')
open('data/secret/token', 'w').write(token)
open('data/master', 'w').write(owner)
open('data/admins', 'w').write(owner + '\n')
open('data/banned', 'w')

print('All files and folders created')
