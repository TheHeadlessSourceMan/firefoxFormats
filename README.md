# firefoxFormats
A command line tool/python library used to access file formats and html schemes registered with firefox

## Command line:

	Usage:
		_firefoxFormats.py [options] [urls]
		
 	Options:
 		--user= ............ select an os user
		--profile= ......... select a firefox profile
		--list ............. list all external formats known to firefox
		--ls ............... list all external formats known to firefox
		--doMime=mimetype,[handler,]url .. open the handler for a mime type
		--doUrl=[handler,]url ... open the handler for a url protocol
		--doExtn=[handler,]url ..open the handler for a file extension type
		--json ............. dump the json configuration to the console
		--ext2mime ......... list file extension -> mimetype mappings
	
	Urls:
		does the same thing as doUrl`
	  
For example, you can easily list everything registered with firefox using:

	_firefoxFormats.py --ls`
	
Or you can open a url with the default handler for that protocol scheme type:

	_firefoxFormats.py --doUrl=whatever://xyz.com/...

Or you can open a local file with the handler for that type:

	_firefoxFormats.py --doExtension=somethingLikeThis.jpg
	
## Current status:

- Works pretty decent on Windows - wouldn't be hard to port to other oses.
- TODO: Use HTTP OPTIONS to figure out the mime type of a http:// url and call --doExtn automatically
- TODO: Allow editing the firefox config to add new schemes, etc.
- Not all details of the file format are handled 
