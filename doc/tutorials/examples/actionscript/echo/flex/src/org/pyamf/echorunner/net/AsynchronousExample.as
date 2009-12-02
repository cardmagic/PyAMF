package org.pyamf.echorunner.net
{
	import flash.events.Event;
	import flash.events.EventDispatcher;
	import flash.events.IOErrorEvent;
	import flash.net.NetConnection;
	import flash.net.Responder;

	public class AsynchronousExample extends EventDispatcher
	{
		private var result:*;
		
		// Gateway connection object
		private var gateway:NetConnection;
		
		public function get data():String
		{
			return result;
		}
		
		public function AsynchronousExample()
		{
			// Setup connection
			gateway = new NetConnection();
			gateway.addEventListener(IOErrorEvent.IO_ERROR, onFail);
			
			// Connect to gateway
			gateway.connect( "http://localhost:8080" );
		}
		
		public function getData():void
		{
			// This var holds the data we want to pass to the remote service.
			var param:String = "Hello World!";
			
			// Set responder property to the object and methods that will receive the 
			// result or fault condition that the service returns.
			var responder:Responder = new Responder( onData, onFail );

			// Call remote service to fetch data
			gateway.call( "echo", responder, param );
		}
		
		private function onData(event:*):void
		{
			result = event;
			
			dispatchEvent(new Event(Event.COMPLETE));
		}
		
		private function onFail(event:*):void
		{
			
		}
		
	}
}