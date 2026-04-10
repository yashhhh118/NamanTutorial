// static/js/main.js — Premium Animation Engine
document.addEventListener('DOMContentLoaded', () => {

    // ==========================================
    // 1. SCROLL PROGRESS BAR
    // ==========================================
    const progressBar = document.createElement('div');
    progressBar.className = 'scroll-progress';
    document.body.prepend(progressBar);

    // ==========================================
    // 2. BACK TO TOP BUTTON
    // ==========================================
    const backToTop = document.createElement('button');
    backToTop.className = 'back-to-top';
    backToTop.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTop.setAttribute('aria-label', 'Back to top');
    document.body.appendChild(backToTop);

    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // ==========================================
    // 3. SCROLL EVENT HANDLER (combined for performance)
    // ==========================================
    let ticking = false;

    function onScroll() {
        const scrollY = window.scrollY;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const nav = document.getElementById('navbar');

        // -- Scroll progress --
        const progress = (scrollY / docHeight) * 100;
        progressBar.style.width = progress + '%';

        // -- Navbar glass effect --
        if (nav) {
            if (scrollY > 50) {
                nav.classList.add('navbar-scrolled');
            } else {
                nav.classList.remove('navbar-scrolled');
            }
        }

        // -- Back to top visibility --
        if (scrollY > 400) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }

        // -- Parallax elements --
        document.querySelectorAll('[data-parallax]').forEach(el => {
            const speed = parseFloat(el.dataset.parallax) || 0.3;
            const rect = el.getBoundingClientRect();
            const centerY = rect.top + rect.height / 2;
            const windowCenter = window.innerHeight / 2;
            const offset = (centerY - windowCenter) * speed;
            el.style.transform = `translateY(${offset}px)`;
        });

        ticking = false;
    }

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(onScroll);
            ticking = true;
        }
    }, { passive: true });

    // ==========================================
    // 4. INTERSECTION OBSERVER — Scroll Reveal
    // ==========================================
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                // Don't unobserve — allow re-triggering on scroll up (optional)
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -60px 0px'
    });

    // Observe all reveal, bounce-in, rotate-in, text-reveal elements
    document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale, .bounce-in, .rotate-in, .text-reveal-container').forEach(el => {
        revealObserver.observe(el);
    });

    // ==========================================
    // 5. ANIMATED COUNTERS (scroll-triggered)
    // ==========================================
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                if (el.dataset.counted) return;
                el.dataset.counted = 'true';

                const target = parseInt(el.dataset.count, 10);
                const suffix = el.dataset.suffix || '';
                const duration = 2000;
                const start = Date.now();

                function updateCounter() {
                    const elapsed = Date.now() - start;
                    const progress = Math.min(elapsed / duration, 1);
                    // Ease-out cubic
                    const eased = 1 - Math.pow(1 - progress, 3);
                    const current = Math.round(target * eased);
                    el.textContent = current.toLocaleString() + suffix;

                    if (progress < 1) {
                        requestAnimationFrame(updateCounter);
                    }
                }

                requestAnimationFrame(updateCounter);
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('[data-count]').forEach(el => {
        counterObserver.observe(el);
    });

    // ==========================================
    // 6. TILT EFFECT ON CARDS
    // ==========================================
    document.querySelectorAll('.tilt-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / centerY * -5;
            const rotateY = (x - centerX) / centerX * 5;

            card.style.transform = `translateY(-10px) perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });

    // ==========================================
    // 7. FLOATING PARTICLES GENERATOR
    // ==========================================
    function createParticles(container, count = 8) {
        if (!container) return;
        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            const size = Math.random() * 8 + 4;
            const colors = ['rgba(255,255,255,0.3)', 'rgba(255,255,255,0.15)', 'rgba(168,223,92,0.3)', 'rgba(255,255,255,0.2)'];
            particle.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation-duration: ${Math.random() * 8 + 6}s;
                animation-delay: ${Math.random() * 4}s;
            `;
            container.appendChild(particle);
        }
    }

    // Add particles to hero and dark sections
    const heroSection = document.querySelector('.hero-gradient');
    if (heroSection) createParticles(heroSection, 12);

    const darkSection = document.querySelector('.bg-darkblue');
    if (darkSection) createParticles(darkSection, 8);

    // ==========================================
    // 8. SMOOTH SCROLL FOR ANCHOR LINKS
    // ==========================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId.length > 1) {
                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    const mobileMenu = document.getElementById('mobile-menu');
                    if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                        mobileMenu.classList.add('hidden');
                    }

                    const headerOffset = 85;
                    const elementPosition = target.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: "smooth"
                    });
                }
            }
        });
    });

    // ==========================================
    // 9. MOBILE MENU TOGGLE
    // ==========================================
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // ==========================================
    // 10. HERO TEXT TYPEWRITER CURSOR
    // ==========================================
    const heroH1 = document.querySelector('.hero-gradient h1');
    if (heroH1) {
        heroH1.style.borderRight = '3px solid rgba(255,255,255,0.7)';
        heroH1.style.paddingRight = '8px';
        // Blink cursor
        let cursorVisible = true;
        setInterval(() => {
            cursorVisible = !cursorVisible;
            heroH1.style.borderRightColor = cursorVisible ? 'rgba(255,255,255,0.7)' : 'transparent';
        }, 600);

        // Remove cursor after 4s
        setTimeout(() => {
            heroH1.style.borderRight = 'none';
            heroH1.style.paddingRight = '0';
        }, 4000);
    }

    // ==========================================
    // 11. SCROLL INDICATOR (bounce arrow in hero)
    // ==========================================
    const scrollIndicator = document.createElement('div');
    scrollIndicator.className = 'absolute bottom-8 left-1/2 -translate-x-1/2 z-30 scroll-indicator hidden md:block';
    scrollIndicator.innerHTML = '<div class="w-8 h-12 border-2 border-white/40 rounded-full flex justify-center pt-2"><div class="w-1.5 h-3 bg-white/60 rounded-full"></div></div>';

    if (heroSection) {
        heroSection.appendChild(scrollIndicator);
        // Fade out on scroll
        window.addEventListener('scroll', () => {
            if (window.scrollY > 100) {
                scrollIndicator.style.opacity = '0';
                scrollIndicator.style.transition = 'opacity 0.5s ease';
            } else {
                scrollIndicator.style.opacity = '1';
            }
        }, { passive: true });
    }

    // ==========================================
    // 12. STAGGER ANIMATION TRIGGER
    // ==========================================
    const staggerObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const children = entry.target.children;
                Array.from(children).forEach((child, i) => {
                    setTimeout(() => {
                        child.style.opacity = '1';
                        child.style.transform = 'translateY(0)';
                    }, i * 120);
                });
            }
        });
    }, { threshold: 0.2 });

    document.querySelectorAll('.stagger-children').forEach(el => {
        // Set initial state for children
        Array.from(el.children).forEach(child => {
            child.style.opacity = '0';
            child.style.transform = 'translateY(30px)';
            child.style.transition = 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
        });
        staggerObserver.observe(el);
    });

    // ==========================================
    // 13. MAGNETIC BUTTON EFFECT
    // ==========================================
    document.querySelectorAll('.magnetic-btn').forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            btn.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px) scale(1.05)`;
        });

        btn.addEventListener('mouseleave', () => {
            btn.style.transform = '';
        });
    });

    // ==========================================
    // 14. INITIAL FIRE — trigger onScroll once
    // ==========================================
    onScroll();
});
