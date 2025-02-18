import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

let signUpBtn = document.querySelector('main .container form #sign-up-btn');
let signInBtn = document.querySelector("main .container form #sign-in-btn");

async function signUpUser(event) {
    event.preventDefault();

    let formData = new FormData(document.getElementById('sign-up-form'));
    let email = formData.get('email');
    let password = formData.get('password');
    let userName = formData.get('username');
    const { data, error } = await supabase.auth.signUp({
        email: email,
        password: password
    });
    if (error) {
        console.error('Error signing up:', error);
        return;
    }

    console.log('Sign up data:', data);
    let session = await userSignIn(email, password);

    if (!session) {
        console.error("Sign-in failed after sign-up.");
        return;
    }
    let userId = session.user.id;
    const { error: insertError } = await supabase.from('Users').insert([
        {
            id: userId,
            email: email,
            userName: userName
        }
    ]);
    if (insertError) {
        console.error('Error inserting user:', insertError);
        return;
    }
    console.log('User inserted successfully');
}

async function userSignIn(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({
        email: email,
        password: password
    });
    if (error) {
        console.error('Error signing in:', error);
        return null;
    }
    console.log('User signed in:', data.user);
    return data;  
}

if (signUpBtn) {
    signUpBtn.addEventListener('click', signUpUser);
}
console.log(signInBtn);

if (signInBtn) {
    signInBtn.addEventListener("click", (event) => {
        event.preventDefault();
        let formData = new FormData(document.getElementById("sign-in-form"));
        let email = formData.get("email");
        let password = formData.get("password");
        console.log("Signing in user with email:", email);
        let session = userSignIn(email, password);
        if (session) {
            window.location.replace("/index.html");
        }
    });
}