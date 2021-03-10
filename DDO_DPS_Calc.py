import itertools
import sys
from tkinter import Tk
from tkinter.filedialog import askopenfilename


# Define a function to parse the Export Data
def parseExport(filePath):
    # Open the selected File and read its contents
    with open(filePath, 'r') as file:
        string = file.read()

    # List of things not to parse out of the data
    exceptions = [" ", "\n", ":", ".", "[", "]"]

    # Define a new string for all the data and remove all the strange characters from it.
    newStr = ""
    for i in string:
        if i == "Â":
            continue
        elif i.isalnum() or i in exceptions:
            newStr += i
        else:
            continue

    # Compile the string into a list to parse it more easily.
    dataList = newStr.split('\n')

    # Return the list of parsed data
    return dataList


# Find the final total of a given stat from the export data
def findStat(stat, exportData):
    for val in exportData:
        if val.split(" ")[0] == stat:
            # For some reason other stats such as HP, PRR, MRR, Fort, AC, Hamp etc... are on the same line...
            # Parse the data into a list seperated at the numbers so we can grab the value we need later.
            data = ["".join(x) for _, x in itertools.groupby(val, key=str.isdigit)]
            # Grab the 3rd value (3rd value is always the final total of the given stat)
            data = [i for i in data if i.isalpha() or i.isdigit()]

            finalStat = data[2]

            return finalStat

        else:
            continue

    # If matching data isn't found return None.
    return None


def findWeaponDice(exportData):
    # Define a list to store weapon data incase user is TWF
    weapons = []
    for val in exportData:
        # Parse the data for the On Hit section (weapon dice is stored on this line)
        if val.split(" ")[0] == "On":
            # Create a list of each seperate dice roll
            data = [i for i in val.split(" ") if i]
            # Remove the first 2 sections of created list (On, and Hit)
            del data[:2]
            # Parse out the damage types (Acid, Untyped, Fire etc...)
            data = [i for i in data if any(c.isdigit() for c in i)]

            weapons.append(data)

    return weapons


def findCritical(exportData):
    # Define a list to store dice data for both normal crits and 19-20 crits
    critDice = []
    critRange = []
    for val in exportData:
        # Parse the data to find the normal critical section
        if val.split(" ")[0] == "Critical":
            # Create a list of each dice roll
            data = [i for i in val.split(" ") if i]
            # Parse out text that isnt part of a roll.
            data = [i for i in data if any(c.isdigit() for c in i)]
            # Append critRange and then remove the first value (the numbers you crit on)
            critRange.append(data[0])
            data.pop(0)

            critDice.append(data)

    critMulti = []
    for i in critDice:
        critMulti.append(i[1])
        i.pop(1)

    return critDice, critMulti, critRange



def findMeleePower(exportData):
    for val in exportData:
        if val.split(" ")[0] == "Melee":
            # The value will be stored in the 3rd spot.
            meleePower = float(val.split()[2])

            return meleePower


def findDoublestrike(exportData):
    for val in exportData:
        if val.split(" ")[0] == "Doublestrike:":
            doubleStrike = val.split()[1]

            return doubleStrike
        else:
            continue

    return None


def findBab(exportData):
    for val in exportData:
        # BAB is stored on the same line as Charisma
        if val.split(" ")[0] == "Cha:":
            # Parse for numbers
            data = ["".join(x) for _, x in itertools.groupby(val, key=str.isdigit)]
            # The BaB value is the last value in the line.
            bab = int(data[-1])

            return bab


def findOffhandInfo(exportData):
    data = []
    for val in exportData:
        if val.split(" ")[0] == "OffHand":
            data.append(val.split()[-1])

        else:
            continue

    offhandChance = data[0]
    offhandDoublestrike = data[1]

    return offhandChance, offhandDoublestrike


def findSneakAttackInfo(exportData):
    data = []
    for val in exportData:
        if val.split(" ")[0] == "Sneak":
            data.append(val.split()[-1])

    data.pop(0)
    if data[0][0] == '0':
        return None
    else:
        return data


def calculateAverageMeleeRolls(weaponDice, meleePower):
    weapons = []
    for weapon in weaponDice:
        damagePerHit = []
        for val in weapon:
            if '[' in val:
                # Parse the string so you can grab the weapon dice
                parsedVal = val.split('[')
                wepDice = parsedVal[0]

                # Parse the string so you can grab the bonus damage
                parsedVal = parsedVal[1].split(']')
                bonus = parsedVal[1]

                # Parse out the inner roll of the dice so it can be calculated.
                # WARNING: THIS WILL BREAK IF THE INNER ROLL BONUS DAMAGE REACHES OR EXCEEDS 10
                # (If that ever happens the game has bigger problems)
                inner = parsedVal[0].split('D')
                innerDice = inner[0]

                # Check if the bow has bonus damage. If so add it otherwise set it to 0.
                if len(inner[1]) >= 2 and len(inner[1]) < 4:
                    innerRoll = inner[1][:-1]
                    innerBonus = inner[1][-1]

                elif len(inner[1]) == 1:
                    innerRoll = inner[1]
                    innerBonus = 0

                else:
                    text = "Either I messed up writing this or the devs added a weapon that is stupidly strong..."
                    return text


                # Calculate the average roll for the inner dice
                innerAverage = float(innerDice) * (float(innerRoll)/2) + int(innerBonus)
                # Calculate the total average damage
                averageTotal = float(wepDice) * float(innerAverage) + float(bonus)

                # Melee Power calculations (need to parse melee power)
                meleePowerCalc = ((100 + meleePower))/100 * averageTotal

                damagePerHit.append(meleePowerCalc)

            else:
                dice = val.split('D')
                if len(dice) == 1:
                    continue
                else:
                    averageDamage = float(dice[0]) * (float(dice[1])/2)
                    damagePerHit.append(averageDamage)

        weapons.append(damagePerHit)

    return weapons


def calculateSneakAttack(sneakDice, meleePower):
    sneakDice = sneakDice[0].split("d")
    dice = int(sneakDice[0])
    roll = int(sneakDice[1][0])
    bonus = int(sneakDice[1][1:])

    sneakDamage = dice * (roll / 2) + bonus

    sneakTotal = (100 + (meleePower * 1.5)) / 100 * sneakDamage

    return sneakTotal


def calculateCritical(critDice, critMulti, meleePower):
    critRolls = []
    for pos, dice in enumerate(critDice):
        damagePerHit = []
        for val in dice:
            if '[' in val:
                # Parse the string so you can grab the weapon dice
                parsedVal = val.split('[')
                wepDice = parsedVal[0]

                # Parse the string so you can grab the bonus damage
                parsedVal = parsedVal[1].split(']')
                bonus = parsedVal[1]

                # Parse out the inner roll of the dice so it can be calculated.
                # WARNING: THIS WILL BREAK IF THE INNER ROLL BONUS DAMAGE REACHES OR EXCEEDS 10
                # (If that ever happens the game has bigger problems)
                inner = parsedVal[0].split('D')
                innerDice = inner[0]

                # Check if the bow has bonus damage. If so add it otherwise set it to 0.
                if len(inner[1]) >= 2 and len(inner[1]) < 4:
                    innerRoll = inner[1][:-1]
                    innerBonus = inner[1][-1]

                elif len(inner[1]) == 1:
                    innerRoll = inner[1]
                    innerBonus = 0

                else:
                    text = "Either I messed up writing this or the devs added a weapon that is stupidly strong..."
                    return text


                # Calculate the average roll for the inner dice
                innerAverage = float(innerDice) * (float(innerRoll)/2) + int(innerBonus)
                # Calculate the total average damage
                averageTotal = (float(wepDice) * float(innerAverage) + float(bonus)) * int(critMulti[pos])

                # Melee Power calculations (need to parse melee power)
                meleePowerCalc = ((100 + meleePower))/100 * averageTotal

                damagePerHit.append(meleePowerCalc)

            else:
                dice = val.split('D')
                if len(dice) == 1:
                    continue
                else:
                    averageDamage = float(dice[0]) * (float(dice[1])/2)
                    damagePerHit.append(averageDamage)

        critRolls.append(damagePerHit)

    return critRolls


def critChance(critRange):
    chances = []

    for i in critRange:
        # There is a .5% chance (0.05) to roll a 19-20
        lowerNumber = i[:-2]
        chances.append(1.05 - ((int(lowerNumber) / 20)) - .05)


    return chances


def calculateAttackSpeed(fightingStyle, speedBonus):
    bab = findBab(parsedExport)

    # Find BaB Stage (1-7) changes at a value of 1, 3, 5, 10, 15, 20, 25
    if bab <= 2:
        babStage = 1
    elif bab > 2 and bab <= 4:
        babStage = 2
    elif bab > 4 and bab <= 9:
        babStage = 3
    elif bab > 9 and bab <= 14:
        babStage = 4
    elif bab > 14 and bab <= 19:
        babStage = 5
    elif bab > 19 and bab <= 24:
        babStage = 6
    elif bab > 24:
        babStage = 7
    else:
        babStage = 0

    # map fighting style to attacks per minute.
    if fightingStyle == "SWF":
        style = 86.6
    elif fightingStyle == "TWF":
        style = 86.66
    elif fightingStyle == "THF":
        style = 86.5
    else:
        print("Invalid Fighting Style")
        style = 0.00
        exit()

    # Calculate the average attacks in a second based on attack speed
    attacksPerSecond = style * (1 + (1.014 ** babStage) * (speedBonus / 100)) / 60

    # Calculate the average attacks in a second including doublestrike
    # averageAttacksPerSecond = attacksPerSecond + (attacksPerSecond * (float(doubleStrike) / 100))
    return attacksPerSecond


def calculateMeleeDamage(damageDice, averageAttacksPerSecond, critRange, critDamage, parsedExport, sneakAttack):
    doublestrike = findDoublestrike(parsedExport)
    critInfo = critChance(critRange)
    critHit = critInfo[0]
    normCrit = sum(critDamage[0])
    highCrit = sum(critDamage[1])

    if sneakAttack:
        for i in damageDice:

            i.append(sneakAttack)


    if len(damageDice) == 1:
        # mainhand base damage = first value of first roll.
        damage = float(damageDice[0][0])
        damageDice[0].pop(0)

        # Crit damage
        total = damage + ((normCrit * critHit) + (highCrit * .05))

        total = total + sum(damageDice[0])

        # Add in doublestrike and attack speed
        dps = total * averageAttacksPerSecond + (averageAttacksPerSecond * (float(doublestrike) / 100))
        return dps

    # For TWF
    else:
        # Get mainhand damage and remove it from the list
        mainHandDamage = float(damageDice[0][0])
        damageDice[0].pop(0)

        # Calculate mainhand crit damage
        mainhandCrit = mainHandDamage + ((normCrit * critHit) + (highCrit * .05))

        # Add in the extra bonus damage from weapon
        mainHandBonus = mainhandCrit + sum(damageDice[0])

        # Add in doublestrike
        mainHandTotal = mainHandBonus * averageAttacksPerSecond + (averageAttacksPerSecond * (float(doublestrike) / 100))

        # Start doing offhand stuff
        offhandHitChance, offhandDoublestrike = findOffhandInfo(parsedExport)
        offhandCritChance = critInfo[2]
        offHandDamage = damageDice[1][0]
        damageDice[1].pop(0)
        offhandNormCrit = sum(critDamage[2])
        offhandHighCrit = sum(critDamage[3])

        # Find Offhand average damage w/crits
        offHandCrits = offHandDamage + ((offhandNormCrit * offhandCritChance) + (offhandHighCrit * .05))

        # Offhand average attacks/second
        offhandAttacksPerSecond = averageAttacksPerSecond * (float(offhandHitChance) / 100)
        # Add in offhand doublestrike
        offHandTotal = offHandCrits + (offhandAttacksPerSecond * float(offhandDoublestrike) / 100)

        # Add offhand bonus damage.
        offHandBonus = offHandTotal + sum(damageDice[1])

        dps = mainHandTotal + (offHandBonus * (float(offhandHitChance) / 100))

        return dps



# -------------------------------------------------------------
# -------------------- < Begin Execution > --------------------
# -------------------------------------------------------------

# Prevent the root window for tkinter from appearing and ask to select file
Tk().withdraw()
filePath = askopenfilename()


# Parse the export data and create a list of it
parsedExport = parseExport(filePath)

# Request speed bonus + fighting style from user and ensure they give a proper input
while True:
    try:
        speedBonus = float(input("Please input your attack speed: "))
        break
    except Exception:
        print("Invalid input please try again!")


validStyles = ["SWF", "THF", "TWF"]
while True:
    style = input("Please input your attack style (abbreviated: SWF, THF or TWF): ")

    if style.upper() not in validStyles:
        print("Invalid input please try again: ")
    else:
        style = style.upper()
        break


while True:
    hasteBoost = input("Haste boost + Prowess?: ")
    hasteBoost = hasteBoost.upper()
    if hasteBoost not in ["YES", "NO"]:
        print("Invalid input please choose Yes, or No")
    else:
        break

# Find the weapon dice and melee power
weaponDice = findWeaponDice(parsedExport)
meleePower = findMeleePower(parsedExport)

if hasteBoost == "YES":
    meleePower += 50
    speedBonus += 30

# Return a list with the damage rolls
damageDice = calculateAverageMeleeRolls(weaponDice, meleePower)

# Check if there are sa dice
sneakDice = findSneakAttackInfo(parsedExport)

if sneakDice:
    sneakAttack = calculateSneakAttack(sneakDice, meleePower)
else:
    sneakAttack = None

# Return a list with Crit Dice & Multi
critDice, critMulti, critRange = findCritical(parsedExport)

# Returns a list with the critical rolls [0] = normal crit [1] = 19-20 crit, [3] & [4] are for TWF normal and 19-20's
critDamage = calculateCritical(critDice, critMulti, meleePower)

# Calculate the average attacks per second and then calculate the average melee damage.
attacksPerSecond = calculateAttackSpeed(style, speedBonus)
DPS = calculateMeleeDamage(damageDice, attacksPerSecond, critRange, critDamage, parsedExport, sneakAttack)

print(f"Average Damage Per Second: {round(DPS)}")

while True:
        wait = input("Type 'exit' to close: ")
        wait = wait.upper()
        if wait != "EXIT":
            continue
        else:
            sys.exit()
