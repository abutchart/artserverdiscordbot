# artserverdiscordbot
A Discord bot for a friend's art commission server 

Due to the adding of features over time, the code has become quite disorganized, which I am not happy about. 

The bot takes artist/creator data from a shared Google Sheet

It has the following functions:
(Copied directly from the help command because I'm lazy)

o!search [username]
Searches for all creator usernames that match search term
- Aliases: se, s
- Type "o!search" with no search term to get a list of all creators
- This command is case insensitive, but if you misspell the search it won't work
- So for the user Onyx#8093:
- o!search onyx | Works
- o!search onxy | Nope
- o!search @Onyx | Mentions work
- o!search Onyx's very cool nickname | So do nicknames
- o!search o | This works, but will bring up multiple search results
o!search tags [tag]
Searches for all creators that have tags that match search term
- Type "o!search tags" with no search term to get a list of all tags
- All of the above information is the same for the tags sub-command, misspellings will not work
o!price [price]
Searches for all creators that have price ranges that match search term
- Aliases: pr, p
- Fairly self-explanatory, just make sure you type a valid number
o!info [number]
Used only when a search brings up multiple results to select an individual creator
- Aliases: in, i
- Example search results:
1 Onyx#8093
2 Hesse#7465
3 OCH Bot 2.0#6335
- So typing "o!info 1" would bring up Onyx's creator info
o!help
A basic help command
- Aliases: h, about, tutorial
o!helpmore
A more detailed help command

It also has some admin commands:
o!status [status]
- Changes the status of the bot
o!prune 
- Checks for differences between the spreadsheet and people with the Creator role
- Largely made obsolete by o!idsync
o!idsync
- Takes the discord tag of each artist on the spreadsheet, gets their id, and adds it to the spreadsheet
- Returns a list of users where the id could not be found and suggests possible matches based off the discriminator
- The stored ids enable the bot to detect when an artist changes their discord tag and updates the spreadsheet accordingly


