import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);
let signUpBtn = document.querySelector('main .container form button[type="submit"]');

async function signInUser() {
    let formData = new FormData(document.getElementById('sign-in-form'));
    let email = formData.get('email');
    let password = formData.get('password');
    const { data, error } = await supabase.auth.signUp({
        email: email,
        password: password
    });
}

function main() {
    if(signUpBtn) {
        signUpBtn.addEventListener('click', signInUser);
    }
}