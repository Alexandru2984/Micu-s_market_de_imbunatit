// Modal Management
document.addEventListener('DOMContentLoaded', function() {
    const modalTriggers = document.querySelectorAll('[data-modal]');
    const closeBtns = document.querySelectorAll('[data-close]');
    const modals = document.querySelectorAll('.modal');


    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden'; 
        }
    }

    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = ''; 
        }
    }

    function closeAllModals() {
        modals.forEach(modal => {
            modal.classList.remove('show');
        });
        document.body.style.overflow = '';
    }

    // add click event listeners to modal triggers
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.getAttribute('data-modal');
            openModal(modalId);
        });
    });

    // add click event listeners to close buttons
    closeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.getAttribute('data-close');
            closeModal(modalId);
        });
    });

    // close modal when clicking outside of modal content
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });

    // handle nested modal triggers
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-modal]')) {
            e.preventDefault();
            const currentModal = e.target.closest('.modal');
            if (currentModal) {
                closeModal(currentModal.id);
            }
            const newModalId = e.target.getAttribute('data-modal');
            setTimeout(() => openModal(newModalId), 300); // small delay for smooth transition
        }
    });
});
