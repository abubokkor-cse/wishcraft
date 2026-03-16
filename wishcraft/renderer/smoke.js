/**
 * WishCraft Smoke Particle System
 * Realistic summoning and dismissal smoke effects
 */

export class SmokeSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.isRunning = false;
        this.animationId = null;

        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        this.canvas.width = this.canvas.offsetWidth * (window.devicePixelRatio || 1);
        this.canvas.height = this.canvas.offsetHeight * (window.devicePixelRatio || 1);
        this.ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
    }

    createParticle(x, y, type = 'summon') {
        const angle = Math.random() * Math.PI * 2;
        const speed = type === 'summon' ? (1 + Math.random() * 3) : (0.5 + Math.random() * 2);
        const size = 8 + Math.random() * 25;

        // Color palette: purple, blue, cyan with some gold sparkle
        const colors = [
            { r: 100, g: 50, b: 255 },   // purple
            { r: 60, g: 30, b: 200 },    // deep purple
            { r: 0, g: 180, b: 255 },    // cyan
            { r: 0, g: 120, b: 200 },    // blue
            { r: 200, g: 150, b: 255 },  // light purple
            { r: 255, g: 200, b: 50 },   // gold sparkle
        ];
        const color = colors[Math.floor(Math.random() * colors.length)];

        return {
            x, y,
            vx: Math.cos(angle) * speed * (type === 'summon' ? -1 : 1),
            vy: -speed * 0.5 + (Math.random() - 0.5) * 2,
            size,
            maxSize: size,
            opacity: 0,
            maxOpacity: 0.3 + Math.random() * 0.4,
            rotation: Math.random() * Math.PI * 2,
            rotationSpeed: (Math.random() - 0.5) * 0.05,
            life: 0,
            maxLife: 40 + Math.random() * 60,
            color,
            type
        };
    }

    /**
     * Summon effect: smoke spirals inward and the genie materializes
     */
    summon(callback) {
        this.particles = [];
        this.isRunning = true;

        const centerX = 125; // avatar center
        const centerY = this.canvas.offsetHeight / 2;
        let frame = 0;
        const totalFrames = 80;

        const emit = () => {
            if (frame < totalFrames * 0.6) {
                // Emit from edges, spiraling inward
                for (let i = 0; i < 4; i++) {
                    const angle = (frame * 0.1) + (i * Math.PI / 2);
                    const radius = 150 - (frame / totalFrames) * 100;
                    const px = centerX + Math.cos(angle) * radius;
                    const py = centerY + Math.sin(angle) * radius;
                    const p = this.createParticle(px, py, 'summon');
                    p.vx = (centerX - px) * 0.02;
                    p.vy = (centerY - py) * 0.02 - 0.5;
                    this.particles.push(p);
                }
            }

            frame++;
            if (frame >= totalFrames) {
                if (callback) callback();
                // Let remaining particles fade out
                setTimeout(() => {
                    this.isRunning = false;
                }, 2000);
            }
        };

        const emitInterval = setInterval(() => {
            if (frame >= totalFrames) {
                clearInterval(emitInterval);
                return;
            }
            emit();
        }, 30);

        this.animate();
    }

    /**
     * Dismiss effect: smoke wraps around avatar and disperses outward
     */
    dismiss(callback) {
        this.particles = [];
        this.isRunning = true;

        const centerX = 125;
        const centerY = this.canvas.offsetHeight / 2;
        let frame = 0;
        const totalFrames = 60;

        const emit = () => {
            if (frame < totalFrames * 0.5) {
                for (let i = 0; i < 5; i++) {
                    const angle = (frame * 0.15) + (i * Math.PI * 2 / 5);
                    const px = centerX + Math.cos(angle) * 30;
                    const py = centerY + Math.sin(angle) * 30;
                    const p = this.createParticle(px, py, 'dismiss');
                    p.vx = Math.cos(angle) * (2 + frame * 0.05);
                    p.vy = Math.sin(angle) * (2 + frame * 0.05) - 1;
                    p.maxOpacity = 0.5;
                    this.particles.push(p);
                }
            }

            frame++;
            if (frame >= totalFrames) {
                if (callback) callback();
                setTimeout(() => {
                    this.isRunning = false;
                }, 1500);
            }
        };

        const emitInterval = setInterval(() => {
            if (frame >= totalFrames) {
                clearInterval(emitInterval);
                return;
            }
            emit();
        }, 30);

        this.animate();
    }

    animate() {
        if (this.animationId) cancelAnimationFrame(this.animationId);

        const loop = () => {
            this.ctx.clearRect(0, 0, this.canvas.offsetWidth, this.canvas.offsetHeight);

            for (let i = this.particles.length - 1; i >= 0; i--) {
                const p = this.particles[i];
                p.life++;

                // Fade in then out
                const lifeRatio = p.life / p.maxLife;
                if (lifeRatio < 0.2) {
                    p.opacity = (lifeRatio / 0.2) * p.maxOpacity;
                } else if (lifeRatio > 0.6) {
                    p.opacity = ((1 - lifeRatio) / 0.4) * p.maxOpacity;
                } else {
                    p.opacity = p.maxOpacity;
                }

                // Move
                p.x += p.vx;
                p.y += p.vy;
                p.vy -= 0.02; // slight upward drift
                p.vx *= 0.98; // drag
                p.vy *= 0.98;
                p.rotation += p.rotationSpeed;
                p.size = p.maxSize * (1 - lifeRatio * 0.3);

                if (p.life >= p.maxLife) {
                    this.particles.splice(i, 1);
                    continue;
                }

                // Draw smoke puff
                this.ctx.save();
                this.ctx.translate(p.x, p.y);
                this.ctx.rotate(p.rotation);
                this.ctx.globalAlpha = p.opacity;

                const gradient = this.ctx.createRadialGradient(0, 0, 0, 0, 0, p.size);
                gradient.addColorStop(0, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, 0.6)`);
                gradient.addColorStop(0.4, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, 0.2)`);
                gradient.addColorStop(1, `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, 0)`);

                this.ctx.fillStyle = gradient;
                this.ctx.beginPath();
                this.ctx.arc(0, 0, p.size, 0, Math.PI * 2);
                this.ctx.fill();
                this.ctx.restore();
            }

            if (this.particles.length > 0 || this.isRunning) {
                this.animationId = requestAnimationFrame(loop);
            } else {
                this.animationId = null;
                this.ctx.clearRect(0, 0, this.canvas.offsetWidth, this.canvas.offsetHeight);
            }
        };

        loop();
    }
}
