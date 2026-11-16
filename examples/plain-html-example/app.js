// Packages load after the page starts. Wait for them, then use them.
await use.ready;

const dayjs = use("dayjs");
const { Chart, registerables } = use("chart.js");
Chart.register(...registerables);

document.getElementById("today").textContent = "Today is " + dayjs().format("dddd, MMMM D, YYYY");

new Chart(document.getElementById("chart"), {
  type: "bar",
  data: {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    datasets: [{ label: "Signups", data: [42, 58, 35, 77, 64, 90], backgroundColor: "#72d6c9", borderRadius: 4 }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: "#e7edf7" } } },
    scales: {
      x: { ticks: { color: "#9da9ba" }, grid: { color: "#2d3848" } },
      y: { ticks: { color: "#9da9ba" }, grid: { color: "#2d3848" }, beginAtZero: true },
    },
  },
});
