(function($) {
    
    $.Loadingdotdotdot = function(el, options) {
        
        var base = this;
        
        base.$el = $(el);
        base.xp = "0";
                
        base.$el.data("Loadingdotdotdot", base);
        
        base.dotItUp = function($element, maxDots) {
            if ($element.text().length == maxDots) {
                $element.text("");
            } else {
                $element.append(".");
            }
            $
        };

	base.dotItUpAgain = function($element, maxDots) {
	    base.xp = 50 + ((base.xp + (50/maxDots)) % 50) ;
            $element.css('background-position',base.xp+'% 0%');
            $
        };
        
        base.stopInterval = function() {    
            clearInterval(base.theInterval);
        };
        
        base.init = function() {
        
            if ( typeof( speed ) === "undefined" || speed === null ) speed = 300;
            if ( typeof( maxDots ) === "undefined" || maxDots === null ) maxDots = 3;
            
            base.speed = speed;
            base.maxDots = maxDots;
                                    
            base.options = $.extend({},$.Loadingdotdotdot.defaultOptions, options);
                        
            base.$el.append("<span>&nbsp;<em></em></span>");
            
            base.$dots = base.$el.find("em");
            base.$loadingText = base.$el.find("span");
            
                        
            base.theInterval = setInterval(base.dotItUp, base.options.speed, base.$dots, base.options.maxDots);
	    // base.the2ndInterval = setInterval(base.dotItUpAgain, base.options.speed/4, base.$el, base.options.maxDots*4);
            
        };
        
        base.init();
    
    };
    
    $.Loadingdotdotdot.defaultOptions = {
        speed: 300,
        maxDots: 3
    };
    
    $.fn.Loadingdotdotdot = function(options) {
        
        if (typeof(options) == "string") {
            var safeGuard = $(this).data('Loadingdotdotdot');
			if (safeGuard) {
				safeGuard.stopInterval();
			}
        } else { 
            return this.each(function(){
                (new $.Loadingdotdotdot(this, options));
            });
        } 
        
    };
    
})(jQuery);
