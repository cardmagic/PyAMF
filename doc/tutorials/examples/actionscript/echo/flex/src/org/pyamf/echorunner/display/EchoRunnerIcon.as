package org.pyamf.echorunner.display
{
    import flash.desktop.Icon;
    import flash.display.Loader;
    import flash.events.Event;
    import flash.net.URLRequest;
      
    /**
     * @author Thijs Triemstra (info@collab.nl)
     */    
    public class EchoRunnerIcon extends Icon
    {		
		private var imageURLs:Array = ['icons/EchoRunnericon16.png','icons/EchoRunnericon32.png',
										'icons/EchoRunnericon48.png','icons/EchoRunnericon128.png'];
										
        public function EchoRunnerIcon():void
        {
            super();
            bitmaps = new Array();
        }
        
        public function loadImages(event:Event = null):void{
        	if(event != null){
        		bitmaps.push(event.target.content.bitmapData);
        	}
        	if(imageURLs.length > 0){
        		var urlString:String = imageURLs.pop();
        		var loader:Loader = new Loader();
        		loader.contentLoaderInfo.addEventListener(Event.COMPLETE,loadImages,false,0,true);
				loader.load(new URLRequest(urlString));
        	} else {
        		var complete:Event = new Event(Event.COMPLETE,false,false);
        		dispatchEvent(complete);
        	}
        }
    }
}