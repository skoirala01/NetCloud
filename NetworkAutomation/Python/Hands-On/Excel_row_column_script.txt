###################################################################
#######################Broadcast Inventory###################################
row = sheet.max_row
col = sheet.max_column
a_row = 2
for j in range(1, col+1):
    bc_invent.cell(1,j).value = sheet.cell(1,j).value

for i in range (2,row+1):
    if '-bc' in str(sheet.cell(i,1).value):
        for j in range (1,col+1):
            bc_invent.cell(a_row,j).value = sheet.cell(i,j).value
        a_row = a_row + 1

################################################################
########Broadcast reachable unreachable ##############################
row = bc_invent.max_row
col = bc_invent.max_column
a_row = 2
b_row = 2
for j in range(1, col+1):
    bc_reach.cell(1,j).value = asa_invent.cell(1,j).value
    bc_unreach.cell(1,j).value = asa_invent.cell(1,j).value
    bc_reach.cell(1,j).font = Font(sz = 12, b = True)
    bc_unreach.cell(1,j).font = Font(sz = 12, b = True)

for i in range (2, row+1):
    if str(bc_invent.cell(i,3).value) == 'ACTIVE':
        for j in range (1,col+1):
            bc_reach.cell(a_row,j).value = bc_invent.cell(i,j).value
        a_row = a_row + 1
    elif str(bc_invent.cell(i,3).value) == 'DEVICE NOT REACHABLE':
        for j in range (1,col+1):
            bc_unreach.cell(b_row,j).value = bc_invent.cell(i,j).value
        b_row = b_row + 1

################################################################
########Extract Config failed for BC##########
row = bc_reach.max_row
col = bc_reach.max_column
a_row = 2
for j in range(1, col+1):
    bc_configfailed.cell(1,j).value = bc_reach.cell(1,j).value
    bc_configfailed.cell(1,j).font = Font(sz = 12, b = True)
   

for i in range (2,row+1):
    if str(bc_reach.cell(i,13).value) != 'PASS':
        for j in range (1,col+1):
            bc_configfailed.cell(a_row,j).value = bc_reach.cell(i,j).value
        a_row = a_row + 1

#############################################################################
################################################################################
