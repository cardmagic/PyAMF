package org.pyamf.echorunner.messages
{
	import flash.events.Event;

	/**
	 * Extends Event to add a field containing the message.
	 */
	public class MessageEvent extends Event
	{
		public var message:String;
		
		public function MessageEvent( type:String, message:String ):void
		{
			this.message = message;
			super( type, false, false );
		}
	}
}