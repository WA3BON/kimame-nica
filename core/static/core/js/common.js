// common.js
document.addEventListener('DOMContentLoaded', function () {
  /* ===============================
     Splide カルーセル
  =============================== */
  const productCarousel = document.querySelector('#product-carousel');
  if (productCarousel) {
    const splide = new Splide('#product-carousel', {
      type: 'loop',
      perPage: 3,
      perMove: 1,
      gap: '1rem',
      arrows: true,
      pagination: false,
      focus: 'center',
      breakpoints: {
        767: { perPage: 1 },
      },
    });

    function updateCenterClass() {
      const slides = document.querySelectorAll('#product-carousel .splide__slide');
      slides.forEach(slide => slide.classList.remove('is-center'));
      const currentIndex = splide.index;
      const centerSlide = slides[currentIndex];
      if (centerSlide) {
        centerSlide.classList.add('is-center');
      }
    }

    splide.on('mounted move', updateCenterClass);
    splide.mount();
  }

  /* ===============================
     フェードイン（Intersection Observer）
  =============================== */
  document.querySelectorAll('.fade-in').forEach((el) => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        el.classList.remove("opacity-0", "translate-y-6");
        el.classList.add("opacity-100", "translate-y-0");
        observer.unobserve(el);
      }
    }, { threshold: 0.4 });

    observer.observe(el);
  });

  /* ===============================
     入力フォームの装飾
  =============================== */
  const inputs = document.querySelectorAll('input, select, textarea');
  inputs.forEach(input => {
    input.classList.add(
      'w-full', 'px-4', 'py-2', 'border', 'border-[#9e7b3b]',
      'rounded-lg', 'focus:outline-none', 'focus:ring-2', 'focus:ring-[#9e7b3b]'
    );
    if (input.tagName === 'TEXTAREA') {
      input.classList.add('h-32', 'resize-none');
    }
  });

  /* ===============================
     Parallax（Alpine.js 用）
  =============================== */
  window.parallax = function () {
    return {
      scrollY: 0,
      bgY: 0,
      leafY: 0,
      init() {
        this.handleScroll();
      },
      handleScroll() {
        this.scrollY = window.scrollY;
        this.bgY = this.scrollY * 0.3;
        this.leafY = this.scrollY * 0.6;
      }
    }
  }
});
