/* ===========================================================
   JOBURA WEALTH®
   NSE Institutional Wealth Management Platform
   Professional Analytics Suite
   Version 2026
=========================================================== */

"use strict";

console.log("JOBURA WEALTH® Platform Loaded");

/* ===========================================================
   LIVE CLOCK
=========================================================== */

function updateClock() {

    const clock = document.getElementById("live-clock");

    if (!clock) return;

    const now = new Date();

    clock.innerHTML =
        now.toLocaleDateString() +
        " | " +
        now.toLocaleTimeString();

}

setInterval(updateClock, 1000);

document.addEventListener("DOMContentLoaded", updateClock);

/* ===========================================================
   SIDEBAR ACTIVE LINK
=========================================================== */

document.addEventListener("DOMContentLoaded", function () {

    const current = window.location.pathname;

    document.querySelectorAll(".sidebar a").forEach(link => {

        if (link.getAttribute("href") === current) {

            link.classList.add("active");

        }

    });

});

/* ===========================================================
   AUTO DISMISS ALERTS
=========================================================== */

function autoDismissAlerts() {

    const alerts = document.querySelectorAll(".auto-dismiss");

    alerts.forEach(alert => {

        setTimeout(() => {

            alert.style.opacity = "0";

            setTimeout(() => {

                alert.remove();

            }, 500);

        }, 5000);

    });

}

document.addEventListener("DOMContentLoaded", autoDismissAlerts);

/* ===========================================================
   LOADING BUTTONS
=========================================================== */

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll("form").forEach(form => {

        form.addEventListener("submit", function () {

            const btn = form.querySelector("button");

            if (btn) {

                btn.dataset.original = btn.innerHTML;

                btn.innerHTML = "Running Simulation...";

                btn.disabled = true;

            }

        });

    });

});

/* ===========================================================
   NUMBER ANIMATION
=========================================================== */

function animateValue(element) {

    const target = Number(element.dataset.value);

    if (isNaN(target)) return;

    let current = 0;

    const increment = target / 60;

    const timer = setInterval(function () {

        current += increment;

        if (current >= target) {

            current = target;

            clearInterval(timer);

        }

        element.innerHTML =
            current.toLocaleString(undefined, {
                maximumFractionDigits: 0
            });

    }, 20);

}

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll(".counter").forEach(el => {

        animateValue(el);

    });

});

/* ===========================================================
   DARK MODE PLACEHOLDER
=========================================================== */

function toggleTheme() {

    document.body.classList.toggle("light-theme");

}

/* ===========================================================
   MARKET STATUS
=========================================================== */

function updateMarketStatus() {

    const market = document.getElementById("market-status");

    if (!market) return;

    const now = new Date();

    const hour = now.getHours();

    if (hour >= 9 && hour < 15) {

        market.innerHTML =
            "🟢 NSE Market Open";

    }

    else {

        market.innerHTML =
            "🔴 NSE Market Closed";

    }

}

document.addEventListener("DOMContentLoaded", updateMarketStatus);

/* ===========================================================
   PORTFOLIO HEALTH COLOUR
=========================================================== */

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll(".health-score").forEach(function (card) {

        const score = Number(card.dataset.score);

        if (score >= 80) {

            card.classList.add("success");

        }

        else if (score >= 60) {

            card.classList.add("warning");

        }

        else {

            card.classList.add("danger");

        }

    });

});

/* ===========================================================
   FUTURE MODULES
=========================================================== */

/*

Future Version 5+

✔ Live NSE Market Feed

✔ Portfolio Rebalancing

✔ AI Chat Assistant

✔ Dividend Calendar

✔ Monte Carlo Progress

✔ Interactive Charts

✔ Notification Centre

✔ Watch List

✔ Portfolio Optimizer

✔ PDF Report Generator

✔ Excel Export

✔ Risk Heat Maps

✔ Sector Exposure Charts

✔ Company Research Search

✔ Retirement Income Timeline

*/