/**
* Template Name: Clinic
* Template URL: https://bootstrapmade.com/clinic-bootstrap-template/
* Updated: Jul 23 2025 with Bootstrap v5.3.7
* Author: BootstrapMade.com
* License: https://bootstrapmade.com/license/
*/

(function() {
  "use strict";

  /**
   * Apply .scrolled class to the body as the page is scrolled down
   */
  function toggleScrolled() {
    const selectBody = document.querySelector('body');
    const selectHeader = document.querySelector('#header');
    if (!selectHeader.classList.contains('scroll-up-sticky') && !selectHeader.classList.contains('sticky-top') && !selectHeader.classList.contains('fixed-top')) return;
    window.scrollY > 100 ? selectBody.classList.add('scrolled') : selectBody.classList.remove('scrolled');
  }

  document.addEventListener('scroll', toggleScrolled);
  window.addEventListener('load', toggleScrolled);

  /**
   * Mobile nav toggle
   */
  const mobileNavToggleBtn = document.querySelector('.mobile-nav-toggle');

  function mobileNavToogle() {
    document.querySelector('body').classList.toggle('mobile-nav-active');
    mobileNavToggleBtn.classList.toggle('bi-list');
    mobileNavToggleBtn.classList.toggle('bi-x');
  }
  if (mobileNavToggleBtn) {
    mobileNavToggleBtn.addEventListener('click', mobileNavToogle);
  }

  /**
   * Hide mobile nav on same-page/hash links
   */
  document.querySelectorAll('#navmenu a').forEach(navmenu => {
    navmenu.addEventListener('click', () => {
      if (document.querySelector('.mobile-nav-active')) {
        mobileNavToogle();
      }
    });

  });

  /**
   * Toggle mobile nav dropdowns
   */
  document.querySelectorAll('.navmenu .toggle-dropdown').forEach(navmenu => {
    navmenu.addEventListener('click', function(e) {
      e.preventDefault();
      this.parentNode.classList.toggle('active');
      this.parentNode.nextElementSibling.classList.toggle('dropdown-active');
      e.stopImmediatePropagation();
    });
  });

  /**
   * Preloader
   */
  const preloader = document.querySelector('#preloader');
  if (preloader) {
    window.addEventListener('load', () => {
      preloader.remove();
    });
  }

  /**
   * Scroll top button
   */
  let scrollTop = document.querySelector('.scroll-top');

  function toggleScrollTop() {
    if (scrollTop) {
      window.scrollY > 100 ? scrollTop.classList.add('active') : scrollTop.classList.remove('active');
    }
  }
  scrollTop.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });

  window.addEventListener('load', toggleScrollTop);
  document.addEventListener('scroll', toggleScrollTop);

  /**
   * Animation on scroll function and init
   */
  function aosInit() {
    AOS.init({
      duration: 600,
      easing: 'ease-in-out',
      once: true,
      mirror: false
    });
  }
  window.addEventListener('load', aosInit);

  /**
   * Initiate glightbox
   */
  const glightbox = GLightbox({
    selector: '.glightbox'
  });

  /**
   * Initiate Pure Counter
   */
  new PureCounter();

  /**
   * Init swiper sliders
   */
  function initSwiper() {
    document.querySelectorAll(".init-swiper").forEach(function(swiperElement) {
      let config = JSON.parse(
        swiperElement.querySelector(".swiper-config").innerHTML.trim()
      );

      if (swiperElement.classList.contains("swiper-tab")) {
        initSwiperWithCustomPagination(swiperElement, config);
      } else {
        new Swiper(swiperElement, config);
      }
    });
  }

  window.addEventListener("load", initSwiper);

  /**
   * Frequently Asked Questions Toggle
   */
  document.querySelectorAll('.faq-item h3, .faq-item .faq-toggle, .faq-item .faq-header').forEach((faqItem) => {
    faqItem.addEventListener('click', () => {
      faqItem.parentNode.classList.toggle('faq-active');
    });
  });

})();

document.addEventListener("DOMContentLoaded", function () {
  async function loadDashboardPartial(url, targetId) {
    const target = document.getElementById(targetId);

    if (!target) {
      return;
    }

    try {
      target.classList.add("dashboard-loading");

      const response = await fetch(url, {
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      });

      if (!response.ok) {
        throw new Error("Failed to load dashboard partial");
      }

      const html = await response.text();
      target.innerHTML = html;
      if (window.initCustomTooltips) {
        window.initCustomTooltips();
      }
    } catch (error) {
      console.error(error);
    } finally {
      target.classList.remove("dashboard-loading");
    }
  }

  document.addEventListener("submit", function (event) {
    const form = event.target.closest(".dashboard-ajax-form");

    if (!form) {
      return;
    }

    event.preventDefault();

    const targetId = form.dataset.target;
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    const url = `${form.action}?${params.toString()}`;

    loadDashboardPartial(url, targetId);
  });

  document.addEventListener("click", function (event) {
    const link = event.target.closest(".dashboard-ajax-link");

    if (!link) {
      return;
    }

    event.preventDefault();

    const targetId = link.dataset.target;
    const url = link.href;

    loadDashboardPartial(url, targetId);
  });

  document.addEventListener("click", function (event) {
    const btn = event.target.closest(".quick-action-btn");
    if (!btn) {
      return;
    }

    event.preventDefault();
    const url = btn.getAttribute("data-action-url");
    const msg = btn.getAttribute("data-confirm-msg");

    if (confirm(msg)) {
      fetch(url, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/json"
        }
      })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        if (data.success) {
          const apptsContainer = document.getElementById("appointments-table-container");
          if (apptsContainer) {
            const activeLink = document.querySelector(".appointments-ajax-link");
            const fetchUrl = activeLink ? activeLink.href : window.location.href;
            fetch(fetchUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
              .then(function (res) { return res.text(); })
              .then(function (html) { apptsContainer.innerHTML = html; });
          } else {
            const patientApptsContainer = document.getElementById("patient-appointments-container");
            if (patientApptsContainer) {
              const activeLink = patientApptsContainer.querySelector(".dashboard-ajax-link");
              const fetchUrl = activeLink ? activeLink.href : window.location.href;
              fetch(fetchUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
                .then(function (res) { return res.text(); })
                .then(function (html) { patientApptsContainer.innerHTML = html; });
            } else {
              window.location.reload();
            }
          }
        } else {
          alert(data.message || "An error occurred.");
        }
      })
      .catch(function (error) {
        console.error(error);
        alert("Failed to perform action.");
      });
    }
  });

  window.initCustomTooltips = function() {
    const elements = document.querySelectorAll('.table-action-btn[title], a[title], button[title]');
    elements.forEach(function (el) {
      const title = el.getAttribute('title');
      if (title) {
        el.setAttribute('data-tooltip', title);
        el.removeAttribute('title');
      }
    });
  };

  // Run initial tooltips parsing
  window.initCustomTooltips();
});