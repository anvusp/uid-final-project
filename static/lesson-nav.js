$(document).ready(function() {
    let btnBack = $('.back-button');
    let btnNext = $('.next-button');

    btnBack.on('click', function(e) {
        e.preventDefault();
        //window.history.back();
        goToPrevious();
    });

    btnNext.on('click', function(e) {
        e.preventDefault();
        console.log('Next button clicked');
        goToNext();
    });

    function goToNext() {
        if (currentIndex < timeline.length - 1) {
            currentIndex++;
            console.log('Current index:', currentIndex);
            renderStep();
        } else {
            alert("Bravo! You have finished the course!");
        }
    }

    function goToPrevious() {
        if (currentIndex > 0) {
            currentIndex--;
            console.log('Current index:', currentIndex);
            renderStep();
        }
    }

    // IMPORTANT: This is a placeholder function. It would go through the timeline and render the appropriate content based on the current index. The back & next buttons are currently broken
    function renderStep() {
        let curr_step = timeline[currentIndex];
    }

});

