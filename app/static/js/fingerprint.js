/**
 * Client-side fingerprinting library for trial abuse prevention
 * Collects browser-specific signals for device identification
 */

class ClientFingerprint {
    static async generate() {
        try {
            const components = await Promise.all([
                this.getCanvasFingerprint(),
                this.getWebGLFingerprint(),
                this.getScreenResolution(),
                this.getTimezone(),
                this.getLanguages(),
                this.getPlugins(),
                this.getFonts(),
                this.getHardwareConcurrency(),
                this.getDeviceMemory(),
                this.getColorDepth(),
                this.getPixelRatio()
            ]);
            
            const fingerprintData = {
                canvas_fingerprint: components[0],
                webgl_fingerprint: components[1],
                screen_resolution: components[2],
                timezone_offset: components[3],
                languages: components[4],
                plugins_hash: components[5],
                fonts_hash: components[6],
                hardware_concurrency: components[7],
                device_memory: components[8],
                color_depth: components[9],
                pixel_ratio: components[10],
                timestamp: Date.now()
            };
            
            // Generate combined client fingerprint hash
            const combinedString = Object.values(fingerprintData).join('|');
            fingerprintData.client_fingerprint_hash = await this.hashString(combinedString);
            
            return fingerprintData;
        } catch (error) {
            console.warn('Fingerprint generation failed:', error);
            return this.getFallbackFingerprint();
        }
    }
    
    static async getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = 280;
            canvas.height = 60;
            
            // Draw distinctive pattern
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            
            ctx.fillStyle = '#069';
            ctx.fillText('Stylize MCP 🎨🔒', 2, 15);
            
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Security fingerprint test', 4, 35);
            
            // Add some geometric shapes
            ctx.globalCompositeOperation = 'multiply';
            ctx.fillStyle = 'rgb(255,0,255)';
            ctx.beginPath();
            ctx.arc(50, 50, 20, 0, Math.PI * 2);
            ctx.fill();
            
            return canvas.toDataURL();
        } catch (error) {
            return 'canvas_error';
        }
    }
    
    static async getWebGLFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) {
                return 'webgl_not_supported';
            }
            
            const result = [];
            
            // Get WebGL parameters
            result.push(gl.getParameter(gl.VERSION));
            result.push(gl.getParameter(gl.SHADING_LANGUAGE_VERSION));
            result.push(gl.getParameter(gl.VENDOR));
            result.push(gl.getParameter(gl.RENDERER));
            
            // Get supported extensions
            const extensions = gl.getSupportedExtensions();
            result.push(extensions ? extensions.sort().join(',') : '');
            
            // Get more detailed parameters
            try {
                result.push(gl.getParameter(gl.MAX_VIEWPORT_DIMS).toString());
                result.push(gl.getParameter(gl.MAX_TEXTURE_SIZE).toString());
                result.push(gl.getParameter(gl.MAX_CUBE_MAP_TEXTURE_SIZE).toString());
                result.push(gl.getParameter(gl.MAX_RENDERBUFFER_SIZE).toString());
            } catch (e) {
                result.push('webgl_params_error');
            }
            
            return result.join('|');
        } catch (error) {
            return 'webgl_error';
        }
    }
    
    static getScreenResolution() {
        try {
            const screen = window.screen;
            return `${screen.width}x${screen.height}x${screen.colorDepth}`;
        } catch (error) {
            return 'screen_error';
        }
    }
    
    static getTimezone() {
        try {
            const offset = new Date().getTimezoneOffset();
            const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            return `${offset}|${timezone}`;
        } catch (error) {
            return new Date().getTimezoneOffset().toString();
        }
    }
    
    static getLanguages() {
        try {
            const languages = navigator.languages || [navigator.language || navigator.userLanguage];
            return languages.join(',');
        } catch (error) {
            return 'lang_error';
        }
    }
    
    static getPlugins() {
        try {
            const plugins = Array.from(navigator.plugins).map(plugin => plugin.name).sort();
            return plugins.join(',');
        } catch (error) {
            return 'plugins_error';
        }
    }
    
    static async getFonts() {
        try {
            // List of common fonts to test
            const fonts = [
                'Arial', 'Arial Black', 'Arial Narrow', 'Arial Rounded MT Bold',
                'Calibri', 'Cambria', 'Comic Sans MS', 'Consolas', 'Courier',
                'Courier New', 'Georgia', 'Helvetica', 'Impact', 'Lucida Console',
                'Lucida Sans Unicode', 'Microsoft Sans Serif', 'Palatino',
                'Times', 'Times New Roman', 'Trebuchet MS', 'Verdana'
            ];
            
            const availableFonts = [];
            const testString = 'mmmmmmmmmmlli';
            const testSize = '72px';
            const defaultWidth = {};
            const defaultHeight = {};
            
            // Create a test element
            const span = document.createElement('span');
            span.style.fontSize = testSize;
            span.style.position = 'absolute';
            span.style.left = '-9999px';
            span.innerHTML = testString;
            document.body.appendChild(span);
            
            // Measure default fonts
            const defaultFonts = ['monospace', 'sans-serif', 'serif'];
            for (const font of defaultFonts) {
                span.style.fontFamily = font;
                defaultWidth[font] = span.offsetWidth;
                defaultHeight[font] = span.offsetHeight;
            }
            
            // Test each font
            for (const font of fonts) {
                let detected = false;
                for (const defaultFont of defaultFonts) {
                    span.style.fontFamily = font + ',' + defaultFont;
                    if (span.offsetWidth !== defaultWidth[defaultFont] || 
                        span.offsetHeight !== defaultHeight[defaultFont]) {
                        detected = true;
                        break;
                    }
                }
                if (detected) {
                    availableFonts.push(font);
                }
            }
            
            document.body.removeChild(span);
            return availableFonts.sort().join(',');
        } catch (error) {
            return 'fonts_error';
        }
    }
    
    static getHardwareConcurrency() {
        try {
            return navigator.hardwareConcurrency || 'unknown';
        } catch (error) {
            return 'hw_error';
        }
    }
    
    static getDeviceMemory() {
        try {
            return navigator.deviceMemory || 'unknown';
        } catch (error) {
            return 'memory_error';
        }
    }
    
    static getColorDepth() {
        try {
            return screen.colorDepth || screen.pixelDepth || 'unknown';
        } catch (error) {
            return 'color_error';
        }
    }
    
    static getPixelRatio() {
        try {
            return window.devicePixelRatio || 'unknown';
        } catch (error) {
            return 'ratio_error';
        }
    }
    
    static async hashString(str) {
        try {
            const encoder = new TextEncoder();
            const data = encoder.encode(str);
            const hashBuffer = await crypto.subtle.digest('SHA-256', data);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        } catch (error) {
            // Fallback hash for older browsers
            let hash = 0;
            if (str.length === 0) return hash.toString();
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32-bit integer
            }
            return hash.toString();
        }
    }
    
    static getFallbackFingerprint() {
        // Minimal fingerprint if full generation fails
        return {
            canvas_fingerprint: 'fallback',
            webgl_fingerprint: 'fallback',
            screen_resolution: this.getScreenResolution(),
            timezone_offset: this.getTimezone(),
            languages: this.getLanguages(),
            plugins_hash: 'fallback',
            fonts_hash: 'fallback',
            hardware_concurrency: this.getHardwareConcurrency(),
            device_memory: this.getDeviceMemory(),
            color_depth: this.getColorDepth(),
            pixel_ratio: this.getPixelRatio(),
            timestamp: Date.now(),
            client_fingerprint_hash: 'fallback_hash'
        };
    }
    
    // Utility method to send fingerprint to server
    static async sendToServer(endpoint = '/api/fingerprint') {
        try {
            const fingerprint = await this.generate();
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(fingerprint)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to send fingerprint to server:', error);
            return null;
        }
    }
    
    // Method to collect and store fingerprint for trial session
    static async collectForTrialSession() {
        const fingerprint = await this.generate();
        
        // Store in session storage for use during API calls
        try {
            sessionStorage.setItem('client_fingerprint', JSON.stringify(fingerprint));
        } catch (error) {
            console.warn('Could not store fingerprint in session storage:', error);
        }
        
        return fingerprint;
    }
    
    // Method to get stored fingerprint
    static getStoredFingerprint() {
        try {
            const stored = sessionStorage.getItem('client_fingerprint');
            return stored ? JSON.parse(stored) : null;
        } catch (error) {
            console.warn('Could not retrieve stored fingerprint:', error);
            return null;
        }
    }
}

// Auto-collect fingerprint when page loads (for trial sessions)
document.addEventListener('DOMContentLoaded', async () => {
    // Only collect if we're on a page that might create trial sessions
    if (window.location.pathname.includes('/web/') || 
        window.location.pathname.includes('/demo') ||
        document.querySelector('[data-collect-fingerprint]')) {
        
        try {
            await ClientFingerprint.collectForTrialSession();
            console.log('Client fingerprint collected for security');
        } catch (error) {
            console.warn('Failed to collect client fingerprint:', error);
        }
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClientFingerprint;
} else {
    window.ClientFingerprint = ClientFingerprint;
}