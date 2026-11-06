// Runs once the page has loaded
document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("expenseChart");
  if (!canvas) return; // Only the dashboard has a chart

  // Ask our Flask API for the category totals (no page reload needed)
  fetch("/api/chart-data")
    .then((response) => response.json())
    .then((payload) => {
      new Chart(canvas, {
        type: "bar",
        data: {
          labels: payload.labels,
          datasets: [
            {
              label: "Amount spent ($)",
              data: payload.data,
              backgroundColor: "#ffbf69",
              borderRadius: 6,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true } },
        },
      });
    })
    .catch((error) => console.error("Could not load chart data:", error));
});