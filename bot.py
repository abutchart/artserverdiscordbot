#Discord Bot for Sam
#Version 2.0.2

import discord, urllib.request, json, re, asyncio
from discord.ext import commands
import os.path
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

TOKEN = '[INSERT TOKEN]'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '[INSERT ID]'
CURRENT_SHEET = '[INSERT SHEET ID]'
RANGE_NAME = 'A5:M'

client = commands.Bot(command_prefix='o!')
#I'm adding my own help commands
client.remove_command('help')

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="2.0 Update!"))
    print("***BOT IS READY***")

#command to change bot status
@client.command()
async def status(ctx, *args):
    admins = ctx.guild.get_role(539216964850155520).members
    botmaster = ctx.guild.get_role(574758348382142464).members
    if ctx.author in admins or ctx.author in botmaster:
        status = ' '.join(args)
        await ctx.send('Changing status to: ' + status)
        await client.change_presence(activity=discord.Game(name=status))
    else:
        await ctx.send('Hey! You aren\'t an admin!! No admin commands for you!!!!!')

#help command
@client.command(aliases=['h', 'about', 'tutorial'])
async def help(ctx):
    embed = discord.Embed(
        title='Help'
    )
    embed.add_field(name='o!search [username]', value='Searches for all creator usernames that match search term', inline=False)
    embed.add_field(name='o!search tags [tag]', value='Searches for all creators that have tags that match search term', inline=False)
    embed.add_field(name='o!price [price]', value='Searches for all creators that have price ranges that match search term', inline=False)
    embed.set_footer(text='This is the basic version of the help command, type o!helpmore to get the detailed version with examples and all that jazz')
    await ctx.send(embed=embed)

#detailed help command
@client.command()
async def helpmore(ctx):
    embed = discord.Embed(
        title='Help'
    )
    embed.add_field(name='o!search [username]', value='Searches for all creator usernames that match search term\n'
                                                      '- Aliases: se, s\n'
                                                      '- Type "o!search" with no search term to get a list of all creators\n'
                                                      '- This command is case insensitive, but if you misspell the search it won\'t work\n'
                                                      '- So for the user Onyx#8093:\n'
                                                      '- o!search onyx | Works\n'
                                                      '- o!search onxy | Nope\n'
                                                      '- o!search @Onyx | Mentions work\n'
                                                      '- o!search Onyx\'s very cool nickname | So do nicknames\n'
                                                      '- o!search o | This works, but will bring up multiple search results', inline=False)
    embed.add_field(name='o!search tags [tag]', value='Searches for all creators that have tags that match search term\n'
                                                      '- Type "o!search tags" with no search term to get a list of all tags\n'
                                                      '- All of the above information is the same for the tags sub-command, misspellings will not work', inline=False)
    embed.add_field(name='o!price [price]', value='Searches for all creators that have price ranges that match search term\n'
                                                  '- Aliases: pr, p\n'
                                                  '- Fairly self-explanatory, just make sure you type a valid number', inline=False)
    embed.add_field(name='o!info [number]', value='Used only when a search brings up multiple results to select an individual creator\n'
                                                 '- Aliases: in, i\n'
                                                 '- Example search results:\n'
                                                  '1 Onyx#8093\n'
                                                  '2 Hesse#7465\n'
                                                  '3 OCH Bot 2.0#6335\n'
                                                  '- So typing "o!info 1" would bring up Onyx\'s creator info', inline=False)
    embed.add_field(name='o!help', value='A basic help command\n'
                                         '- Aliases: h, about, tutorial', inline=False)
    embed.add_field(name='o!helpmore', value='A more detailed help command', inline=False)
    await ctx.send(embed=embed)

async def getJson():
    with urllib.request.urlopen(
            'https://spreadsheets.google.com/feeds/cells/' + SPREADSHEET_ID + '/1/public/basic?alt=json') as url:
        data = json.load(url)

    return data['feed']['entry']

#admin command - check inconsistenties between the spreadsheet and the creators on the server
@client.command()
async def prune(ctx):
    admins = ctx.guild.get_role(539216964850155520).members
    botmaster = ctx.guild.get_role(574758348382142464).members
    if ctx.author in admins or ctx.author in botmaster:
        creatorRole = ctx.guild.get_role(538925113249234944).members
        creators = []
        for member in creatorRole:
            creators.append(str(member))

        data = await getJson()

        creatorsOnSheet = []
        # get all usernames (located in column B)
        for entry in data[16:]:
            if entry['title']['$t'].startswith('B'):
                creatorsOnSheet.append(entry['content']['$t'])

        roleNotSheet = [x for x in creators if x not in creatorsOnSheet]
        sheetNotRole = [x for x in creatorsOnSheet if x not in creators]

        await ctx.send('**Has role but not on sheet:** \n' + '\n'.join(
            roleNotSheet) + '\n\n' + '**On sheet but does not have role:** \n' + '\n'.join(sheetNotRole))
    else:
        await ctx.send('Hey! You aren\'t an admin!! No admin commands for you!!!!!')

async def authenticate():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


#runs through spreadsheet and adds id if missing or changed
@client.command()
async def idsync(ctx):
    creators = ctx.guild.get_role(538925113249234944).members
    creatorsDict = {}
    discriminatorDict = {}

    service = build('sheets', 'v4', credentials=await authenticate())
    sheet = service.spreadsheets()

    for creator in creators:
        creatorsDict[str(creator)] = creator.id
        discriminatorDict[creator.discriminator] = str(creator)
    data = await getJson()

    rows = []
    #All of the values in the id column must be unique for the username updating thing to work
    #kind of an ugly solution but it works
    notListedDiscriminator = '                         '

    embed = discord.Embed(
        title='Could Not Find Id Of:',
        colour=discord.Colour.red()
    )

    for entry in data[16:]:
        coordinate = entry['title']['$t']
        name = entry['content']['$t']

        if coordinate.startswith('B'):
            if name in creatorsDict.keys():
                print('Updating id of: ' + name)
                rows.append(
                    {
                        'values': [
                            {
                                'userEnteredValue': {
                                    'stringValue': str(creatorsDict[name])
                                }
                            }
                        ]
                    }
                )

            else:
                notListedDiscriminator += '*'
                print(name + ' does not have creator role')
                rows.append(
                    {
                        'values': [
                            {
                                'userEnteredValue': {
                                    'stringValue': '(Not Listed)' + notListedDiscriminator
                                }
                            }
                        ]
                    }
                )
                possibleMatch = [discriminatorDict[discrim] for discrim in discriminatorDict.keys() if name[-4:] == discrim]
                if possibleMatch:
                    print('Possible Match: ' + possibleMatch[0])
                    embed.add_field(name=name, value='Possible match: ' + possibleMatch[0], inline=False)
                else:
                    embed.add_field(name=name, value='No possible match found', inline=False)

        # Sheets API Request
        body = {
            'requests': [
                {
                    'updateCells': {
                        'rows': rows,
                        'fields': '*',
                        'range': {
                            'sheetId': CURRENT_SHEET,
                            'startRowIndex': 4,
                            'endRowIndex': len(rows) + 4,
                            'startColumnIndex': 12,
                            'endColumnIndex': 13,
                        }
                    }
                }
            ]
        }

    print(sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute())
    if len(embed.fields) > 0:
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title='Synced Successfully',
            colour=discord.Colour.green()
        )
        await ctx.send(embed=embed)


#checks if creator usernames have changed, if they have, updates database automatically
@client.event
async def on_user_update(before, after):
    logChannel = client.get_channel(633887091914309652)

    data = await getJson()
    idDict = {}

    # maps all users (column B) to each id (column M)
    tempUserVar = ''
    for entry in data[16:]:
        if entry['title']['$t'].startswith('B'):
            tempUserVar = entry['content']['$t']
        elif entry['title']['$t'].startswith('M'):
            idDict[entry['content']['$t']] = tempUserVar

    for x, id in enumerate(idDict.keys(), start=4):
        if str(after.id) == id and str(after) != idDict[id]:
            print(str(after) + ' has changed their username from ' + str(before) + ' to ' + str(after))
            print('Updating database')

            creds = None
            # The file token.pickle stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server()
                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)

            # build sheet
            service = build('sheets', 'v4', credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()

            # gdrive api request - update cell value with new username
            body = {
                'requests': [
                    {
                        'updateCells': {
                            'rows': [
                                {
                                    'values': [
                                        {
                                            'userEnteredValue': {
                                                'stringValue': str(after)
                                            }
                                        }
                                    ]
                                }
                            ],
                            'fields': '*',
                            'start': {
                                'columnIndex': 1,
                                'rowIndex': x,
                                'sheetId': CURRENT_SHEET
                            }
                        }
                    }
                ]
            }
            try:
                sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
                row = str(x+1)
                message = 'Updated Database at Row ' + row
                print(message)

                #fancy embed message for och log channel
                embed = discord.Embed(
                    title='Creator Has Changed Name',
                    colour=discord.Colour.green()
                )
                embed.add_field(name='Original Name:', value=str(before), inline=False)
                embed.add_field(name='New Name:', value=str(after), inline=False)
                embed.add_field(name=message,
                                value='https://docs.google.com/spreadsheets/d/' + SPREADSHEET_ID + '/edit#gid=' + CURRENT_SHEET + '&range=B' + row,
                                inline=False)
                await logChannel.send(embed=embed)
            except:
                embed = discord.Embed(
                    title='ERROR: Creator has changed name but could not update database',
                    colour=discord.Colour.red()
                )
                embed.add_field(name='Original Name:', value=str(before), inline=False)
                embed.add_field(name='New Name:', value=str(after), inline=False)
                await logChannel.send(embed=embed)

            break


multipleSearchUsersDict = {}

#search command
@client.command(aliases=['info', 'in', 'i', 'se', 's'])
async def search(ctx, *args):
    #blank field - output all users
    if len(args) == 0:
        print('Blank Field - Output All Tags')
        usersList = []

        data = await getJson()

        # get all usernames (located in column B)
        for entry in data[16:]:
            if entry['title']['$t'].startswith('B'):
                usersList.append(entry['content']['$t'])

        await multipleSearchResults(usersList, ctx, colour=discord.Colour.blue())

    #searching by tag instead of username
    elif args[0] == 'tags':
        #blank field - outputs all unique tags
        if len(args) == 1:
            print('Blank Field - Output All Tags')
            tagsList = []

            data = await getJson()

            # get all tags (located in column K)
            for entry in data[16:]:
                if entry['title']['$t'].startswith('K'):
                    tags = entry['content']['$t'].split(',')
                    for tag in tags:
                        tagsList.append(tag.strip().title())

            tagsList = sorted(list(set(tagsList)), key=str.lower)[2:]
            print(tagsList)

            embed = discord.Embed(
                title='All Unique Tags (Alphabetical Order)',
                colour=discord.Colour.blue()
            )

            embed.add_field(name='0-9', value='\n'.join([tag for tag in tagsList if tag[0].isdigit()]), inline=False)
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                value = [tag for tag in tagsList if tag[0] == letter]
                if not len(value) == 0:
                    embed.add_field(name=letter, value='\n'.join(value), inline=False)

            embed.set_footer(text='Type o!search tags [tag] to search for a specific tag')
            await ctx.send(embed=embed)


        #otherwise search by user input as normal
        else:
            data = await getJson()
            tagDict = {}

            # maps all tags (column K) to each user (column B)
            tempUserVar = ''
            for entry in data[16:]:
                if entry['title']['$t'].startswith('B'):
                    tempUserVar = entry['content']['$t']
                elif entry['title']['$t'].startswith('K'):
                    tagDict[tempUserVar] = entry['content']['$t']

            userInput = ' '.join(args[1:])

            matchingTags = {k: v for k, v in tagDict.items() if userInput.lower() in v.lower()}
            print(userInput)

            if len(matchingTags) == 0:
                await searchError(ctx)
            else:
                matchingUsers = list(matchingTags.keys())
                matchingTags = list(matchingTags.values())
                await multipleSearchResults(matchingUsers, ctx, colour=discord.Colour.blue(), embedValueList=matchingTags)

    else:
        userInput = ' '.join(args)
        usersDict = {}

        data = await getJson()

        #get all usernames (located in column B)
        for entry in data[16:]:
            if entry['title']['$t'].startswith('B'):
                usersDict[entry['content']['$t']] = entry['title']['$t']

        #multiple users index selection
        if userInput.isdigit():
            print('User Selected Index ' + userInput + ': ' + multipleSearchUsersDict[userInput])
            await oneSearchResult(multipleSearchUsersDict[userInput], usersDict, data, ctx)
        #mentions
        elif userInput.startswith('<@') and userInput.endswith('>'):
            user = client.get_user(int(userInput[2:-1]))
            if user:
                print(str(user) + ' Mentioned')
                await oneSearchResult(str(user), usersDict, data, ctx)
        else:
            #get list of users that match user search
            matchingUsers = [i for i in usersDict.keys() if userInput.lower() in i.lower()]

            #if no results, try searching nicknames
            if len(matchingUsers) == 0:
                creatorRole = ctx.guild.get_role(538925113249234944)
                creatorNicknameDict = {}
                for member in creatorRole.members:
                    creatorNicknameDict[member.display_name] = str(member)
                matchingNicknames = [i for i in creatorNicknameDict.keys() if userInput.lower() in i.lower()]
                for user in matchingNicknames:
                    creator = creatorNicknameDict[user]
                    if creator in usersDict.keys():
                        matchingUsers.append(creator)

            #multiple search results
            if len(matchingUsers) > 1:
                await multipleSearchResults(matchingUsers, ctx, colour=discord.Colour.blue())
            #one search result
            elif len(matchingUsers) == 1:
                await oneSearchResult(matchingUsers[0], usersDict, data, ctx)
            #no search results
            else:
                await searchError(ctx)

async def searchError(ctx):
    print('No Matches Found')
    embed = discord.Embed(
        title='ERROR:',
        colour=discord.Colour.red()
    )
    embed.add_field(name='Could not find requested data', value='Are you sure that you typed everything correctly?',
                    inline=False)
    await ctx.send(embed=embed)

async def oneSearchResult(matchedUser, usersDict, data, ctx):
    print('Match found: '+ matchedUser)
    embedTitleList = ['Discord Tag', 'Other Contacts', 'Examples', 'Other Profiles', 'Commission Types', 'Average Commission Price', 'Currency', 'Payment Method', 'NSFW?', 'Tags', 'Price Sheet']
    embed = discord.Embed(
        title='Search Results',
        colour=discord.Colour.blue()
    )
    #find matched user's pfp
    for member in ctx.channel.members:
        if str(member) == matchedUser:
            embed.set_thumbnail(url=member.avatar_url)

    coordinate = usersDict[matchedUser]
    embedTitleListIndex = 0
    for entry in data[16:]:
        searchedCoordinate = entry['title']['$t']
        content = entry['content']['$t']
        #get all user data - located in the same row
        if searchedCoordinate.endswith(coordinate[1:]) and len(coordinate) == len(searchedCoordinate) and not (searchedCoordinate.startswith('A') or searchedCoordinate.startswith('M')):
            #if it has a price sheet, display it (located in column L, image link starts with "https" or "http")
            if searchedCoordinate.startswith('L') and content.startswith('http'):
                embed.set_image(url=content)
                embed.add_field(name='Price Sheet', value='See Below', inline=False)
            else:
                embed.add_field(name=embedTitleList[embedTitleListIndex], value=discord.utils.escape_markdown(content), inline=False)
                embedTitleListIndex += 1
    await ctx.send(embed=embed)

async def multipleSearchResults(matchedUsers, ctx, colour, embedValueList=None):
    print('Multiple Matches Found: ')
    print(matchedUsers)

    embed = discord.Embed(
        title='Search Results',
        colour=colour
    )

    #embed only accepts 25 field entries
    #if embed has > 25 fields
    if len(matchedUsers) > 25:
        # list of embed lists
        embedPages = []
        # list to hold 25 or fewer fields
        embedPageFields = []

        for i, user in enumerate(matchedUsers, start=1):
            #if number of fields <= 25, add fields to first embed
            if i < 25:
                #add fields to embed to send initially
                embed.add_field(name=str(i) + ' ' + discord.utils.escape_markdown(user), value=embedValueList[i - 1] if embedValueList else '...', inline=False)
                #add fields to stored embed
                embedPageFields.append((str(i), discord.utils.escape_markdown(user)))
            elif i == 25:
                embed.add_field(name=str(i) + ' ' + discord.utils.escape_markdown(user), value=embedValueList[i - 1] if embedValueList else '...', inline=False)
                # repeat above storage process
                embedPageFields.append((str(i), discord.utils.escape_markdown(user)))
                # add stored embed to list of embeds
                embedPages.append(embedPageFields)
                # clear stored embed
                embedPageFields = []
            #on every 25 entries
            elif i % 25 == 0:
                embedPageFields.append((str(i), discord.utils.escape_markdown(user)))
                embedPages.append(embedPageFields)
                embedPageFields = []
            else:
                embedPageFields.append((str(i), discord.utils.escape_markdown(user)))
            #add to index storage
            multipleSearchUsersDict[str(i)] = user

        #add last few entries
        embedPages.append(embedPageFields)
        numOfPages = len(embedPages)
        embed.set_footer(
            text='Type o!info[number] to select full creator info | Page 1/{} | Click reaction to change pages'.format(
                numOfPages))
        #send inital unedited embed
        message = await ctx.send(embed=embed)
        await message.add_reaction('▶')
        i = 0

        def check(reaction, user):
            return not user == client.user and message.id == reaction.message.id and (str(reaction.emoji) == '▶' or str(reaction.emoji) == '◀')

        while True:
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                print('TIMEOUT, REACTIONS REMOVED')
                await message.clear_reactions()
                break
            else:
                if reaction.emoji == '▶':
                    i += 1
                    embedPage = embedPages[i]
                    embed.clear_fields()
                    for j, field in enumerate(embedPage):
                        embed.add_field(name=field[0] + ' ' + field[1], value=embedValueList[(j + (25 * i))] if embedValueList else '...', inline=False)
                    embed.set_footer(
                        text='Type o!info[number] to select full creator info | Page {}/{} | Click reaction to change pages'.format(
                            i + 1, numOfPages))
                    await message.clear_reactions()
                    await message.edit(embed=embed)
                    # if last page, add back button and nothing else
                    if i + 1 == len(embedPages):
                        await message.add_reaction('◀')
                    else:
                        await message.add_reaction('◀')
                        await message.add_reaction('▶')
                elif reaction.emoji == '◀':
                    i -= 1
                    embedPage = embedPages[i]
                    embed.clear_fields()
                    for j, field in enumerate(embedPage):
                        embed.add_field(name=field[0] + ' ' + field[1], value=embedValueList[(j + (25 * i))] if embedValueList else '...', inline=False)
                    embed.set_footer(
                        text='Type o!info[number] to select full creator info | Page {}/{} | Click reaction to change pages'.format(
                            i + 1, numOfPages))
                    await message.clear_reactions()
                    await message.edit(embed=embed)
                    # if first page, add forward button and nothing else
                    if i == 0:
                        await message.add_reaction('▶')
                    else:
                        await message.add_reaction('◀')
                        await message.add_reaction('▶')
    else:
        for i, user in enumerate(matchedUsers, start=1):
            embed.add_field(name=str(i) + ' ' + discord.utils.escape_markdown(user), value=embedValueList[i - 1] if embedValueList else '...', inline=False)
            multipleSearchUsersDict[str(i)] = user
        embed.set_footer(text='Type o!info[number] to select full creator info')
        await ctx.send(embed=embed)


#search by price command
@client.command(aliases=['pr', 'p'])
async def price(ctx, arg):
    if arg[0] == '$':
        arg = arg[1:]

    embed = discord.Embed(
        title='ERROR:',
        colour=discord.Colour.red()
    )
    embed.set_footer(text='Use the format o!price [number]')

    if not arg.isdigit():
        print('Invalid Input')
        embed.add_field(name='Invalid Input', value='Numbers only, please.')
        await ctx.send(embed=embed)
    elif int(arg) < 0:
        print('Invalid Input')
        embed.add_field(name='Invalid Input', value='\"If I pay the artist negative dollars, they\'ll pay me! Genius!!!\" -' + ctx.author.name)
        await ctx.send(embed=embed)
    elif int(arg) > 999999:
        print('Invalid Input')
        embed.add_field(name='Invalid Input',value='What are you commissioning? A house?')
        await ctx.send(embed=embed)
    else:
        data = await getJson()

        priceDict = {}

        # maps all prices (column G) to each user (column B)
        tempUserVar = ''
        for entry in data[16:]:
            if entry['title']['$t'].startswith('B'):
                tempUserVar = entry['content']['$t']
            elif entry['title']['$t'].startswith('G'):
                priceDict[tempUserVar] = entry['content']['$t']

        matchingPrices = {k: v for k, v in priceDict.items() if await withinRange(arg, v)}
        matchingUsers = list(matchingPrices.keys())
        matchingPrices = list(matchingPrices.values())

        await multipleSearchResults(matchingUsers, ctx, colour=discord.Colour.gold(), embedValueList=matchingPrices)

async def withinRange(num, string):
    num = int(num)
    string = string.replace('<$5', '0 5')
    string = string.replace('>', ' 999999')
    string = string.replace('+', ' 999999')
    string = string.replace('Free', '0')

    regex = re.compile(r'\d+')
    matched = re.findall(regex, string)
    matched = list(map(int, matched))

    if len(matched) == 0:
        return False
    elif min(matched) <= num <= max(matched):
        return True
    else:
        return False

client.run(TOKEN)
