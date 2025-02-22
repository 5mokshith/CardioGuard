import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;
export const supabase = createClient(supabaseUrl, supabaseKey);


export async function signUpUser(email, password, userName) {
    const { data, error } = await supabase.auth.signUp({
        email: email,
        password: password
    });

    if (error) {
        console.error('Error signing up:', error);
        return null;
    }

    console.log('Sign up data:', data);
    let session = await userSignIn(email, password);

    if (!session) {
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
        console.error('Error inserting user:', insertError);
        return null;
    }

    console.log('User inserted successfully');
    return session;  // Return session to be used in transitions
}

export async function userSignIn(email, password) {
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
