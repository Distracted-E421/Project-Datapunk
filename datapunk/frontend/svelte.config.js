import adapter from '@sveltejs/adapter-auto';

/** @type {import('@sveltejs/kit').Config} */

const config = {
	kit: {
		adapter: adapter(),
		files: {
			routes: 'src/routes',
			lib: 'src/lib'
		}
	}
};

export default config;
