function loadTimetable(day) {
    document.getElementById('dayTitle').textContent = day;
    fetch(`/api/timetable?region=${encodeURIComponent(selectedRegion)}&day=${day}`)
        .then(response => response.json())
        .then(data => {
            renderTimetable(data);
            renderListings(data);
        });
}

function renderTimetable(data) {
    const ctx = document.getElementById('timetableChart').getContext('2d');
    
    if (window.timetableChart instanceof Chart) {
        window.timetableChart.destroy();
    }

    const rcNames = data.map(rc => rc.name);
    const datasets = data.map((rc, index) => ({
        label: rc.name,
        data: [{x: [rc.start, rc.end], y: rc.name}],
        backgroundColor: getRandomColor(),
        barPercentage: 0.8
    }));

    window.timetableChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: rcNames,
            datasets: datasets
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear',
                    position: 'top',
                    min: 0,
                    max: 24,
                    ticks: {
                        stepSize: 1,
                        callback: function(value) {
                            return value.toString().padStart(2, '0') + ':00';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Hours (24-hour format)'
                    }
                },
                y: {
                    title: {
                        display: false,
                    },

                    ticks: {
                        autoSkip: false,
                        padding: 3
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: (tooltipItems) => {
                            return tooltipItems[0].dataset.label;
                        },
                        label: (tooltipItem) => {
                            const rc = data[tooltipItem.dataIndex];
                            return `Open: ${rc.start.toString().padStart(2, '0')}:00 - ${rc.end.toString().padStart(2, '0')}:00`;
                        }
                    }
                }
            }
        }
    });
}

function renderListings(data) {
    const listingsDiv = document.getElementById('listings');
    listingsDiv.innerHTML = data.map(rc => `
        <div class="listing">
            <h3>${rc.name}</h3>
            <p>Address: ${rc.address}</p>
            <p>Postal Code: ${rc.postal_code}</p>
            <p>Hours: ${rc.start}:00 - ${rc.end}:00</p>
        </div>
    `).join('');
}

function getRandomColor() {
    const r = Math.floor(Math.random() * 200 + 55);
    const g = Math.floor(Math.random() * 200 + 55);
    const b = Math.floor(Math.random() * 200 + 55);
    return `rgba(${r}, ${g}, ${b}, 0.7)`;
}

// Load Monday's timetable by default
loadTimetable('Monday');