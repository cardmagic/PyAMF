package org.pyamf.echorunner
{
	import flash.desktop.DockIcon;
	import flash.desktop.NativeApplication;
	import flash.desktop.NotificationType;
	import flash.desktop.SystemTrayIcon;
	import flash.display.NativeMenu;
	import flash.display.NativeMenuItem;
	import flash.events.Event;
	import flash.events.InvokeEvent;
	import flash.events.MouseEvent;
	
	import flexunit.flexui.TestRunnerBase;
	
	import mx.core.WindowedApplication;
	import mx.events.FlexEvent;
	
	import org.pyamf.echorunner.display.DisplayManager;
	import org.pyamf.echorunner.messages.MessageCenter;
	import org.pyamf.echorunner.messages.MessageEvent;
	
	/**
	 * @author Thijs Triemstra (info@collab.nl)
	 */	
	public class EchoRunner extends WindowedApplication
	{
		private var displayManager:	DisplayManager;
		private var messageCenter:	MessageCenter;
		private const idleTime:		int = 15; //seconds

		public function EchoRunner()
		{
			displayManager = new DisplayManager();
			messageCenter = new MessageCenter();
			
			// Listen to the source of the messages
			messageCenter.addEventListener( MessageCenter.NEW_MESSAGE, onMessage );
			
			// listen for application invocations (through the commandline)
			this.addEventListener( InvokeEvent.INVOKE, onInvoke );
			this.addEventListener( FlexEvent.CREATION_COMPLETE, onCreationComplete );
		}
	
		private function onCreationComplete( event:FlexEvent ):void
		{
			if( NativeApplication.supportsDockIcon ) {
				var dockIcon:DockIcon = NativeApplication.nativeApplication.icon as DockIcon;
				NativeApplication.nativeApplication.addEventListener( InvokeEvent.INVOKE, undock );
				dockIcon.menu = createIconMenu();
			}
			else if ( NativeApplication.supportsSystemTrayIcon )
			{
				var sysTrayIcon:SystemTrayIcon = NativeApplication.nativeApplication.icon as SystemTrayIcon;
				sysTrayIcon.tooltip = "EchoRunner";
				sysTrayIcon.addEventListener( MouseEvent.CLICK, undock );
				sysTrayIcon.menu = createIconMenu();
			}
			
			// Detect user presence
			NativeApplication.nativeApplication.idleThreshold = idleTime;
			NativeApplication.nativeApplication.addEventListener( Event.USER_IDLE, onIdle );
			NativeApplication.nativeApplication.addEventListener( Event.USER_PRESENT, onPresence );
			NativeApplication.nativeApplication.autoExit = false;
		}
	
		private function onInvoke( invokeEvent:InvokeEvent ):void
		{
		    var now:String = new Date().toTimeString();
		    logEvent("Invoke event received: " + now);
		            
		    if( invokeEvent.currentDirectory != null ){
		        logEvent("Current directory=" + invokeEvent.currentDirectory.nativePath);
		    } else {
		        logEvent("--no directory information available--");
		    }
		            
		    if( invokeEvent.arguments.length > 0 )
		    {
		        logEvent("Arguments: " + invokeEvent.arguments);
		    } else {
		        logEvent("--no arguments--");
		    }
		}
		
		/** "Docking" and icon control functions **/				
		private function dock( event:Event = null ):void
		{
			stage.nativeWindow.visible = false;
			//NativeApplication.nativeApplication.icon.bitmaps = [clock.bitmapData];
		}	
		
		private function undock( event:Event = null ):void
		{
			stage.nativeWindow.visible = true;
			NativeApplication.nativeApplication.icon.bitmaps = [];
		}
		
		private function changeIcon():void
		{
			//NativeApplication.nativeApplication.icon.bitmaps = [clock.bitmapData];				
		}
		
		/** Notification function **/		
		private function notify():void
		{
			if( NativeApplication.supportsDockIcon ){
				var dock:DockIcon = NativeApplication.nativeApplication.icon as DockIcon;
  				dock.bounce( NotificationType.CRITICAL );
			}
			else if ( NativeApplication.supportsSystemTrayIcon )
			{
				stage.nativeWindow.notifyUser( NotificationType.CRITICAL );
			}
		}
		
		// When the computer is idle, don't remove the messages
		private function onIdle(event:Event):void
		{
			displayManager.pauseExpiration();
			trace("Idling.");
		}
		
		// On return, let windows expire again
		private function onPresence(event:Event):void
		{
			displayManager.resumeExpiration();
			trace("Resuming.");
		}
		
		// Pass the message to the display controller
		private function onMessage( event:MessageEvent ):void
		{
			displayManager.displayMessage( event.message );
			//notify();
		}
		
		/** Menu creation and menu functions **/
		private var startCommand:NativeMenuItem = new NativeMenuItem("Start");
		private var pauseCommand:NativeMenuItem = new NativeMenuItem("Pause");
		
		private function createIconMenu():NativeMenu
		{
			var iconMenu:NativeMenu = new NativeMenu();
			iconMenu.addItem( startCommand );
			startCommand.addEventListener( Event.SELECT, runTests );
			iconMenu.addItem( pauseCommand );
			pauseCommand.addEventListener( Event.SELECT, pauseTests );
			iconMenu.addEventListener( Event.DISPLAYING, setMenuCommandStates );
			
			return iconMenu;
		}
		
		private function runTests( event:Event ):void
		{
			messageCenter.startFeed();
		}
		
		private function pauseTests( event:Event ):void
		{
			messageCenter.stopFeed();
		}
		
		private function exitApp(event:Event):void
		{
			NativeApplication.nativeApplication.exit();
		}
		
		private function setMenuCommandStates( event:Event ):void
		{
			//startCommand.enabled = goButton.startState;
			//pauseCommand.enabled = !goButton.startState;
		}
		
		private function logEvent( entry:String ):void
		{
		    //displayManager.displayMessage( entry );
		}
		
	}
}