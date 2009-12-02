package org.pyamf.echorunner.messages
{
	import flash.events.Event;
	import flash.events.EventDispatcher;
	
	import flexunit.framework.AssertionFailedError;
	import flexunit.framework.Test;
	import flexunit.framework.TestCase;
	import flexunit.framework.TestSuite;
	import flexunit.textui.TestRunner;
	
	import org.pyamf.echorunner.net.AsynchronousTest;
	import org.pyamf.echorunner.net.PythonSocket;
	
	/**
	 * The MessageCenter sends and receives unit test messages
	 * over a socket.
	 * 
	 * @author: Thijs Triemstra (info@collab.nl)
	 */
	public class MessageCenter extends EventDispatcher
	{
		private var server:PythonSocket;
		
		private var _totalTests:uint = 0;
		private var _totalErrors:uint = 0;
		private var _totalFailures:uint = 0;
		private var _numTestsRun:uint = 0;
		
		public var test:Test;
		
		public static const NEW_MESSAGE:String = "newMessage";
		
		public function MessageCenter():void
		{
			// Connect to server
			server = new PythonSocket();
			
			// Listen for log updates
			server.addEventListener( PythonSocket.CONNECTED, startState );
			server.addEventListener( PythonSocket.DISCONNECTED, startState );
			server.addEventListener( PythonSocket.LOG_UPDATE, logUpdate );
		}
		
		private function logUpdate( event:LogEvent ):void
		{
			// Display log message
			var message:String = event.message;
			var messageEvent:MessageEvent = new MessageEvent( NEW_MESSAGE, message );
			dispatchEvent( messageEvent );
		}
		
		public function startFeed():void
		{
			stopState();
			
			// Setup test runner
			_numTestsRun = 0;
			
			var suite:TestSuite = new TestSuite();
			suite.addTest( AsynchronousTest.suite());
			test = suite;
			
			startTest();
			
			// Start feed
			//server.write( "start" );
		}
		
		public function stopFeed():void
		{
			startState();
			
			// Stop feed
			//server.write( "stop" );
		}
		
		private function startState( event:Event=null ):void
		{
			//start_btn.enabled = true;
			//stop_btn.enabled = false;
		}
		
		private function stopState( event:Event=null ):void
		{
			//start_btn.enabled = false;
			//stop_btn.enabled = true;
		}
		
		public function startTest():void
		{
			if( test != null )
			{
				_totalTests = test.countTestCases();
				
				//progressBar.minimum = 0;
				//testFailures.dataProvider = new Array();
				//allTestsList.dataProvider = new Array();
				
				updateLabels();
				
				flexunit.textui.TestRunner.run( test, onTestEnd );
			}
		}		
		
		private function updateLabels():void
		{
			var txt:String = "Run: " + _numTestsRun.toString()+"/"+_totalTests.toString();
			txt += "\nErrors: " + _totalErrors.toString();
			txt += "\nFailures: "+_totalFailures.toString();
			var messageEvent:MessageEvent = new MessageEvent( NEW_MESSAGE, txt );
			dispatchEvent( messageEvent );
		}
		
		private function updateProgress():void
		{
			//progressBar.setProgress( _numTestsRun, _totalTests );
			
			if( _totalErrors > 0 || _totalFailures > 0 )
				trace("neutral");//progressBar.setStyle("barColor",0xFF0000);
		}
		
		private function addFailureToList( test:Test, error:Error ):void
		{
			var t:TestCase = test as TestCase;
			if( t != null )
			{
				var label:String = label+t.methodName+" - "+t.className;
				onTestSelected();
				var messageEvent:MessageEvent = new MessageEvent( NEW_MESSAGE, label );
				dispatchEvent( messageEvent );
			}
		}
		
		private function onTestSelected():void
		{
			//var list:List = (testTabs.selectedIndex == 0) ? testFailures : allTestsList;
			
			//if( list.selectedItem != null )
			//	if( list.selectedItem.error != null )
			//		stackTrace.text = list.selectedItem.error.getStackTrace();
			//	else
			//		stackTrace.text = "";
			
		}
		
		private function addTestToList( success:Boolean, test:Test, error:Error = null ):void
		{
			var t:TestCase = test as TestCase;
			if( t != null )
			{
				var label:String = ( success ) ? "[PASS] " : "[FAIL] ";
				label += label+t.methodName+" - "+t.className;
				onTestSelected();
				var messageEvent:MessageEvent = new MessageEvent( NEW_MESSAGE, label );
				dispatchEvent( messageEvent );
			}			
		}
		
		public function onTestStart( test:Test=null ) : void
		{
		}
		
		public function onTestEnd( test:Test=null ) : void
		{
			_numTestsRun++;
			
			updateLabels();
			updateProgress();
		}
		
		public function onAllTestsEnd() : void
		{
			//progressBar.setProgress(100,100);
			if( _totalErrors == 0 && _totalFailures == 0 )
				trace("done");//progressBar.setStyle("barColor",0x00FF00);
		}
		
		public function onSuccess( test:Test ):void
		{
			addTestToList( true, test );
		}
		
 	   	public function onError( test:Test, error:Error ) : void
 	   	{
 	   		_totalErrors++;
 	   		addFailureToList( test, error );
 	   		addTestToList( false, test, error );
 	   	}
 	   	
		public function onFailure( test:Test, error:AssertionFailedError ) : void
		{
			_totalFailures++;
			addFailureToList( test, error );
			addTestToList( false, test, error );
		}
		
	}
}