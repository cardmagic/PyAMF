package org.pyamf.echorunner.messages
{
	import flash.events.Event;

	/**
	 * Extends Event to add a field containing the log message.
	 */
	public class LogEvent extends Event
	{
		public var message:String;
		
		public function LogEvent( type:String, message:String ):void
		{
			this.message = message;
			super( type, false, false );
		}
	}
}