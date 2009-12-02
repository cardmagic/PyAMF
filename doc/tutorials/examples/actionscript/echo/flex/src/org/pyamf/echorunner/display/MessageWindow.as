package org.pyamf.echorunner.display
{
	import flash.display.NativeWindow;
	import flash.display.NativeWindowInitOptions;
	import flash.display.NativeWindowSystemChrome;
	import flash.display.NativeWindowType;
	import flash.display.Sprite;
	import flash.display.StageAlign;
	import flash.display.StageScaleMode;
	import flash.events.Event;
	import flash.events.MouseEvent;
	import flash.filters.DropShadowFilter;
	import flash.text.TextField;
	import flash.text.TextFormat;

	/**
	 * A lightweight window to display the message.
	 */
	public class MessageWindow extends NativeWindow
	{
		public var timeToLive:uint;
		private static const stockWidth:int = 300;
		private static const padding:int = 10;
		private var manager:DisplayManager;
		private const format:TextFormat = new TextFormat( "Arial", 12, 0 );
					
		public function MessageWindow(message:String, manager:DisplayManager):void
		{
			this.manager = manager;
			
			var options:NativeWindowInitOptions = new NativeWindowInitOptions();
			options.type = NativeWindowType.LIGHTWEIGHT;
			options.systemChrome = NativeWindowSystemChrome.NONE;
			options.transparent = true;
			super(options);
			
			stage.addEventListener(MouseEvent.MOUSE_DOWN,onClick);
			stage.align = StageAlign.TOP_LEFT;
			stage.scaleMode = StageScaleMode.NO_SCALE;
			
			manager.addEventListener( DisplayManager.LIFE_TICK, lifeTick, false, 0, true );
			width = MessageWindow.stockWidth + (padding*2);
			
			var textDisplay:TextField = new TextField();
			textDisplay.text = message;
			textDisplay.wordWrap = true;
			format.bold = false;
			textDisplay.setTextFormat(format);
			stage.addChild(textDisplay);
			textDisplay.x = 5 + padding;
			textDisplay.y = 5 + padding;
			textDisplay.width = width - 10;
			height = textDisplay.textHeight + 10 + (padding*2);

			draw();	
			alwaysInFront = true;
		}
		
		private function onClick( event:MouseEvent ):void
		{
			close();
		}
		
		public function lifeTick( event:Event ):void
		{
			timeToLive--;
			if(timeToLive < 1){
				close();
			}
		}
		
		public override function close():void
		{
			manager.removeEventListener( DisplayManager.LIFE_TICK,lifeTick,false );
			super.close();
		}
		
		private function draw():void
		{
			// Create the drop shadow filter for the window background.
			var shadow:DropShadowFilter = new DropShadowFilter();
			shadow.distance = 2;
			shadow.angle = 5;
			shadow.blurX = 10;
			shadow.blurY = 5;
			shadow.knockout = true;
			
			var background:Sprite = new Sprite();
			with( background.graphics )
			{
				beginFill( 0xFFFFFF, 0.97);
					drawRect( padding-2, padding-2, width-padding, height-padding );
				endFill();
			}
			// Add dropshadow
			background.filters = [shadow];
			
			var foreground:Sprite = new Sprite();
			with( foreground.graphics )
			{
				beginFill( 0xFFFFFF, 1);
					drawRect( padding, padding, width-padding-5, height-padding-2 );
				endFill();
			}
			
			stage.addChildAt(background, 0);
			stage.addChildAt(foreground, 1);
		}
		
		public function animateY( endY:int ):void
		{
			var dY:Number;
			var animate:Function = function( event:Event ):void
			{
				dY = (endY - y)/4
				y += dY;
				if( y <= endY){
					y = endY;
					stage.removeEventListener( Event.ENTER_FRAME, animate );
				}
			}
			stage.addEventListener(Event.ENTER_FRAME,animate);
		}
		
	}
}