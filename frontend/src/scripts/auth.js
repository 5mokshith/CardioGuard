import { createClient } from '@supabase/supabase-js';
import { displayMessage, hideLoadingAnimation, showLoadingAnimation } from './utils';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;
export const supabase = createClient(supabaseUrl, supabaseKey);

export async function signUpUser(email, password, userName) {
    showLoadingAnimation();

    const { data, error } = await supabase.auth.signUp({
        email: email,
        password: password
    });

    if (error) {
        displayMessage("Error signing up. Please try again.", true);
        hideLoadingAnimation();
        console.error('Error signing up:', error);
        return null;
    }

    console.log('Sign up data:', data);
    // Sign in the user after signup
    let session = await userSignIn(email, password);
    if (!session) {
        displayMessage("Error signing in after sign-up. Please try again.", true);
        hideLoadingAnimation();
        console.error("Sign-in failed after sign-up.");
        return null;
    }

    let userId = session.user.id;
    const { error: insertError } = await supabase.from('users').insert([
        {
            id: userId,
            email: email,
            name: userName
        }
    ]);

    if (insertError) {
        displayMessage("Error inserting user data. Please try again.", true);
        hideLoadingAnimation();
        console.error('Error inserting user:', insertError);
        return null;
    }

    displayMessage("User inserted successfully");
    console.log('User inserted successfully');
    hideLoadingAnimation();
    return session;  // Return session to be used in transitions
}

export async function userSignIn(email, password) {
    showLoadingAnimation();

    const { data, error } = await supabase.auth.signInWithPassword({
        email: email,
        password: password
    });

    if (error) {
        displayMessage("Error signing in. Please try again.", true);
        console.error('Error signing in:', error);
        hideLoadingAnimation();
        return null;
    }

    displayMessage("User signed in successfully");
    console.log('User signed in:', data.user);
    hideLoadingAnimation();
    window.location = "./dashboard.html"
    return data;
}
