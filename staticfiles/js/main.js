document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('skillsForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const analysisDiv = document.getElementById('analysis');
    const jobsDiv = document.getElementById('jobs');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading state
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        
        try {
            const formData = new FormData(form);
            
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            
            const data = await response.json();
            
            // Hide loading state
            loading.classList.add('hidden');
            results.classList.remove('hidden');
            
            // Display analysis results
            let analysisHTML = '<h2 class="text-2xl font-semibold text-gray-800 mb-4">Career Analysis</h2>';
            data.analysis.forEach(result => {
                analysisHTML += `
                    <div class="mb-4 p-4 border rounded-lg">
                        <h3 class="text-xl font-medium text-indigo-600">${result.title}</h3>
                        <div class="mt-2">
                            <div class="w-full bg-gray-200 rounded-full h-2.5">
                                <div class="bg-indigo-600 h-2.5 rounded-full" style="width: ${result.percentage}%"></div>
                            </div>
                            <p class="text-sm text-gray-600 mt-1">${result.percentage}% match</p>
                        </div>
                        <div class="mt-2">
                            <p class="text-sm text-gray-700"><span class="font-medium">Matching Skills:</span> ${result.matching.join(', ')}</p>
                            <p class="text-sm text-gray-700"><span class="font-medium">Missing Skills:</span> ${result.missing.join(', ')}</p>
                        </div>
                    </div>
                `;
            });
            analysisDiv.innerHTML = analysisHTML;
            
            // Display job listings
            let jobsHTML = '<h2 class="text-2xl font-semibold text-gray-800 mb-4">Relevant Job Listings</h2>';
            data.live_jobs.forEach(job => {
                jobsHTML += `
                    <div class="p-4 border rounded-lg hover:bg-gray-50">
                        <h3 class="text-lg font-medium text-indigo-600">${job.title}</h3>
                        <p class="text-gray-600">${job.company_name}</p>
                        <p class="text-sm text-gray-500">${job.location} • ${job.source}</p>
                        <a href="${job.url}" target="_blank" class="text-indigo-600 hover:text-indigo-800 text-sm">View Job</a>
                    </div>
                `;
            });
            jobsDiv.innerHTML = jobsHTML;
            
        } catch (error) {
            console.error('Error:', error);
            loading.classList.add('hidden');
            results.classList.remove('hidden');
            analysisDiv.innerHTML = '<p class="text-red-600">An error occurred while analyzing your skills.</p>';
        }
    });
}); 