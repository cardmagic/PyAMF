package org.pyamf.echorunner.net
{
	import flash.events.Event;
	
	import flexunit.framework.TestCase;
	import flexunit.framework.TestSuite;

	public class AsynchronousTest extends TestCase
	{
		public function AsynchronousTest( method:String )
		{
			super(method);
		}
		
		public function testGetData():void
		{
			var asynchronous:AsynchronousExample = new AsynchronousExample();
			asynchronous.addEventListener( Event.COMPLETE, addAsync(onData, 2000) );
			asynchronous.getData();
		}
		
		private function onData(event:Event):void
		{
			assertNotNull(event.target.data);
		}
		
		public static function suite():TestSuite
		{
			var suite:TestSuite = new TestSuite();
			suite.addTest( new AsynchronousTest("testGetData") );
			suite.addTest( new AsynchronousTest("testGetData") );
			return suite;
		}
		
	}
}