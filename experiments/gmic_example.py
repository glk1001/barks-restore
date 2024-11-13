import gmic

# gmic.run("help smooth")
# help(gmic)
gmic.run("input ./junk.png smooth 10,0,1,1,2 output junk-smooth.png")
