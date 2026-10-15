import React from 'react';
import {createRoot} from 'react-dom/client';
import CucumberApp from '../app/CucumberApp';
import initial from './bootstrap.json';
import '../app/globals.css';
createRoot(document.getElementById('root')!).render(<CucumberApp initial={initial as any}/>);
